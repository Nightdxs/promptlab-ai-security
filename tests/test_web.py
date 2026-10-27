"""Interfaz local: servidores y modelos programados; no ejecuta un LLM."""
import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from promptlab.web import GuidedBackend, LabState, LocalServer


class WebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = LabState(Path(self.tmp.name) / "runs")
        self.server = LocalServer(("127.0.0.1", 0), self.state)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def request(self, method, path, payload=None, trusted=True, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        sent = {"Content-Type": "application/json"}
        if trusted:
            sent.update(Origin=f"http://127.0.0.1:{self.server.server_port}",
                        **{"X-PromptLab-Token": self.state.token})
        sent.update(headers or {})
        body = json.dumps(payload).encode() if payload is not None else None
        connection.request(method, path, body, sent)
        response = connection.getresponse()
        raw = response.read()
        status, mime = response.status, response.getheader("Content-Type", "")
        connection.close()
        return status, json.loads(raw) if "json" in mime else raw

    def payload(self, kind="attack", mode="guided", configs=None):
        case = next(c for c in self.state.presets if c["kind"] == kind)
        return {"case_id": case["id"], "mode": mode, "configs": configs or ["C0", "C2P"]}

    def wait_job(self, job_id):
        until = time.monotonic() + 8
        while time.monotonic() < until:
            job = self.state.snapshot(job_id)
            if job["state"] not in ("running", "cancelling"):
                return job
            time.sleep(.02)
        self.fail("El servidor de prueba no terminó")

    def test_static_files_host_and_path_boundaries(self):
        status, raw = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"PromptLab", raw)
        self.assertEqual(self.request("GET", "/../.env")[0], 404)
        self.assertEqual(self.request("GET", "/", headers={"Host": "attacker.invalid"})[0], 403)

    def test_mutations_require_same_origin_and_session_token(self):
        payload = self.payload()
        self.assertEqual(self.request("POST", "/api/jobs", payload, trusted=False)[0], 403)
        self.assertEqual(self.request("POST", "/api/jobs", payload, headers={"Origin": "https://attacker.invalid"})[0], 403)
        self.assertEqual(self.request("POST", "/api/jobs", payload, headers={"X-PromptLab-Token": "wrong"})[0], 403)
        self.assertEqual(self.request("POST", "/api/jobs", payload, headers={"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.state.jobs, {})

    def test_guided_comparison_preserves_real_tool_effects_and_synthetic_label(self):
        with patch("promptlab.web.OllamaBackend") as model:
            status, result = self.request("POST", "/api/jobs", self.payload())
            self.assertEqual(status, 202)
            job = self.wait_job(result["id"])
            model.assert_not_called()
        self.assertEqual(job["state"], "completed")
        self.assertTrue(job["manifest"]["synthetic_no_llm"])
        trials = {trial["config"]: trial for trial in job["trials"]}
        self.assertTrue(trials["C0"]["canary_disclosure_observed"])
        self.assertTrue(trials["C0"]["outbox"])
        self.assertFalse(trials["C2P"]["canary_disclosure_observed"])
        self.assertEqual(trials["C2P"]["outbox"], [])
        self.assertTrue(any(item["type"] == "tool_result" for item in job["live"]))
        self.assertEqual(self.request("GET", "/api/jobs/" + result["id"] + "/download")[0], 200)
        archived = self.state.archived(job["run_id"])
        self.assertEqual(archived["trials"], job["trials"])

    def test_guided_mode_ignores_edits_and_parallel_runs_are_rejected(self):
        with patch.object(self.state, "_execute"):
            payload = self.payload()
            payload.update(user_task="edited", payload="edited")
            status, result = self.request("POST", "/api/jobs", payload)
            self.assertEqual(status, 202)
            self.assertNotEqual(self.state.snapshot(result["id"])["case"]["payload"], "edited")
            self.assertEqual(self.request("POST", "/api/jobs", payload)[0], 409)

    def test_model_edits_are_isolated_from_corpus_and_permissions(self):
        original = self.state.presets[0]["payload"]
        payload = self.payload(mode="ollama")
        payload.update(payload="Texto de prueba <script>alert(1)</script>", user_task="Resume briefing.")
        with patch.object(self.state, "_execute"):
            status, result = self.request("POST", "/api/jobs", payload)
        self.assertEqual(status, 202)
        self.assertIn("<script>", self.state.snapshot(result["id"])["case"]["payload"])
        self.assertEqual(self.state.presets[0]["payload"], original)

    def test_missing_or_invalid_case_and_options_are_rejected(self):
        for payload in ([], {"mode": "guided", "configs": ["C0"], "case_id": "../../file"},
                        {**self.payload(), "configs": ["C0", "C0"]},
                        {**self.payload(mode="ollama"), "payload": ""}):
            self.assertEqual(self.request("POST", "/api/jobs", payload)[0], 400)
        self.assertEqual(self.state.jobs, {})

    def test_changed_model_identity_disables_comparison_rates(self):
        case = next(c for c in self.state.presets if c["kind"] == "benign")
        counter = []
        def describe():
            counter.append(1)
            return {"local_model": {"digest": "before" if len(counter) == 1 else "after"},
                    "requested_model": "test", "server": {"version": "test"},
                    "model_capabilities": ["tools"], "model_details": {}}
        with patch("promptlab.web.OllamaBackend") as factory:
            factory.return_value.describe.side_effect = describe
            factory.return_value.chat.side_effect = GuidedBackend(case).chat
            status, result = self.request("POST", "/api/jobs", self.payload("benign", "ollama", ["C0"]))
            self.assertEqual(status, 202)
            job = self.wait_job(result["id"])
        self.assertEqual(job["state"], "failed")
        self.assertFalse(job["manifest"]["model_identity_verified"])
        rows = json.loads((self.state.output / job["run_id"] / "summary.json").read_text())
        self.assertTrue(all(row["utility_lower_bound"] is None for row in rows))

    def test_cancel_discards_pending_tool_calls_and_preserves_partial_report(self):
        entered, release = threading.Event(), threading.Event()
        def blocked_chat(*args):
            entered.set()
            release.wait(timeout=3)
            return {"message": {"role": "assistant", "content": "", "tool_calls": [{"function": {
                "name": "enviar_correo", "arguments": {"destinatario": "ana@equipo.invalid", "asunto": "x", "cuerpo": "x"}}}]}}
        with patch("promptlab.web.OllamaBackend") as factory:
            factory.return_value.describe.return_value = {"local_model": {"digest": "same"}}
            factory.return_value.chat.side_effect = blocked_chat
            status, result = self.request("POST", "/api/jobs", self.payload("benign", "ollama"))
            self.assertEqual(status, 202)
            self.assertTrue(entered.wait(timeout=2))
            self.assertEqual(self.request("POST", "/api/jobs/" + result["id"] + "/cancel", {})[0], 200)
            release.set()
            job = self.wait_job(result["id"])
        self.assertEqual(job["state"], "cancelled")
        self.assertFalse(job["manifest"]["completed"])
        self.assertEqual(len(job["trials"]), 1)
        self.assertEqual(job["trials"][0]["outbox"], [])
        self.assertIsNone(job["trials"][0]["attack_success"])


if __name__ == "__main__":
    unittest.main()
