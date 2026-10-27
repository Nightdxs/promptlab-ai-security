"""Contrato HTTP completo con servidor de respuestas programadas. No ejecuta un LLM."""
import contextlib
import io
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from promptlab.__main__ import main
from promptlab.core import ScriptedDemo
from promptlab.dataset import load_cases


class FakeOllama(HTTPServer):
    chat_calls = 0
    tag_calls = 0
    change_digest = False
    remote = False


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, value):
        raw = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/tags":
            self.server.tag_calls += 1
            digest = "changed" if self.server.change_digest and self.server.tag_calls > 1 else "test-digest"
            self.send_json({"models": [{"name": "test-local", "digest": digest}]})
        elif self.path == "/api/version":
            self.send_json({"version": "test-only"})
        else:
            self.send_error(404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/show":
            self.send_json({"capabilities": ["tools"],
                            "remote_host": "https://example.invalid" if self.server.remote else ""})
        elif self.path == "/api/chat":
            self.server.chat_calls += 1
            reply = ScriptedDemo().chat(body["messages"], body["tools"], body["options"]["seed"])
            reply.update(model="test-local", done=True, done_reason="stop")
            self.send_json(reply)
        else:
            self.send_error(404)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.server = FakeOllama(("127.0.0.1", 0), Handler)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        case = next(case for case in load_cases() if case["kind"] == "attack")
        self.corpus = self.root / "case.jsonl"
        self.corpus.write_text(json.dumps(case))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=2)
        self.tmp.cleanup()

    def run_cli(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return main(["run", "--model", "test-local", "--base-url",
                         f"http://127.0.0.1:{self.server.server_port}",
                         "--configs", "C0", "C2P", "--corpus", str(self.corpus),
                         "--output", str(self.root / "results"), "--timeout", "2"])

    def test_full_http_tool_loop_and_cli_outputs(self):
        self.assertEqual(self.run_cli(), 0)
        folder = next((self.root / "results").iterdir())
        manifest = json.loads((folder / "manifest.json").read_text())
        self.assertTrue(manifest["model_identity_verified"])
        trials = [json.loads(line) for line in (folder / "trials.jsonl").read_text().splitlines()]
        results = {trial["config"]: trial for trial in trials}
        self.assertTrue(results["C0"]["attack_success"])
        self.assertFalse(results["C2P"]["attack_success"])
        self.assertTrue(all(trial["attack_exposed"] for trial in trials))
        self.assertEqual(self.server.chat_calls, 8)

    def test_changed_model_disables_comparison_rates_in_all_formats(self):
        self.server.change_digest = True
        self.assertEqual(self.run_cli(), 2)
        folder = next((self.root / "results").iterdir())
        self.assertIn("IDENTIDAD DEL MODELO NO VERIFICADA", (folder / "SUMMARY.md").read_text())
        rows = json.loads((folder / "summary.json").read_text())
        self.assertTrue(all(row["asr_lower_bound"] is None for row in rows))
        self.assertIn("invalid_model_identity", (folder / "summary.csv").read_text())

    def test_remote_alias_never_receives_task_messages(self):
        self.server.remote = True
        self.assertEqual(self.run_cli(), 2)
        self.assertEqual(self.server.chat_calls, 0)
        self.assertFalse((self.root / "results").exists())
