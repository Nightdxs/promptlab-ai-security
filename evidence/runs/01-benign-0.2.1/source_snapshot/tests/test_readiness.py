import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from promptlab.__main__ import main
from promptlab.core import ScriptedDemo, run_trial
from promptlab.dataset import DEFAULT_CORPUS, load_cases
from promptlab.diagnostics import diagnose
from promptlab.reporting import write_report


class ReadinessTests(unittest.TestCase):
    def test_offline_diagnostic_makes_no_network_requests(self):
        with patch("promptlab.diagnostics.OllamaBackend") as backend:
            report = diagnose(DEFAULT_CORPUS)
        backend.assert_not_called()
        self.assertTrue(report["ready_for_offline_demo"])
        self.assertIsNone(report["model_metadata_verified"])
        self.assertFalse(report["inference_tested"])

    def test_diagnostic_model_check_never_calls_chat(self):
        with patch("promptlab.diagnostics.OllamaBackend") as backend:
            backend.return_value.describe.return_value = {"local_model": {"digest": "test"}}
            report = diagnose(DEFAULT_CORPUS, "test-local")
        backend.return_value.chat.assert_not_called()
        self.assertTrue(report["model_metadata_verified"])
        self.assertFalse(report["inference_tested"])

    def test_missing_corpus_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = diagnose(Path(tmp) / "missing.jsonl")
        self.assertFalse(report["ready_for_offline_demo"])
        self.assertTrue(report["errors"])

    def test_bad_model_and_remote_url_return_diagnostic_errors(self):
        for model, url in (("test:cloud", "http://127.0.0.1:11434"),
                           ("test-local", "http://example.invalid")):
            with self.subTest(model=model), contextlib.redirect_stdout(io.StringIO()) as output:
                code = main(["doctor", "--model", model, "--base-url", url])
                self.assertEqual(code, 2)
                self.assertFalse(json.loads(output.getvalue())["model_metadata_verified"])

    def test_benign_pilot_filters_before_selecting_and_covers_three_tasks(self):
        with patch("promptlab.__main__.OllamaBackend"), \
             patch("promptlab.__main__.save_execution", return_value=0) as save, \
             contextlib.redirect_stdout(io.StringIO()):
            code = main(["run", "--model", "test-local", "--kind", "benign", "--limit-per-kind", "3"])
        self.assertEqual(code, 0)
        cases = save.call_args.args[1]
        self.assertEqual(len(cases), 3)
        self.assertTrue(all(case["kind"] == "benign" for case in cases))
        self.assertEqual({case["task"] for case in cases}, {"summary", "lookup", "mail"})

    def test_empty_selection_never_contacts_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "attack.jsonl"
            case = next(case for case in load_cases() if case["kind"] == "attack")
            corpus.write_text(json.dumps(case), encoding="utf-8")
            with patch("promptlab.__main__.OllamaBackend") as backend, \
                 contextlib.redirect_stderr(io.StringIO()):
                code = main(["run", "--model", "test-local", "--kind", "benign", "--corpus", str(corpus)])
            self.assertEqual(code, 2)
            backend.assert_not_called()

    def test_event_export_separates_blocked_attempt_and_executed_violation(self):
        case = next(case for case in load_cases() if case["kind"] == "attack")
        trials = [run_trial(case, ScriptedDemo(), config, 42) for config in ("C0", "C2P")]
        with tempfile.TemporaryDirectory() as tmp:
            write_report(Path(tmp), trials, synthetic=True)
            events = [json.loads(line) for line in (Path(tmp) / "events.jsonl").read_text().splitlines()]
        self.assertEqual(len(events), sum(len(trial["events"]) for trial in trials))
        blocked = [event for event in events if event["decision"] == "blocked"]
        self.assertTrue(blocked)
        self.assertTrue(all(event["authorization_violation"] for event in blocked))
        self.assertTrue(all(not event["policy_violation_executed"] for event in blocked))
        executed = [event for event in events if event["policy_violation_executed"]]
        self.assertTrue(executed)
        self.assertTrue(all(event["config"] == "C0" for event in executed))
        self.assertTrue(all(event["synthetic_no_llm"] is True for event in events))
        for event in events:
            trial = trials[event["trial_index"] - 1]
            self.assertEqual(trial["events"][event["event_index"] - 1]["tool"], event["tool"])

    def test_unverified_identity_stays_visible_in_event_export(self):
        case = next(case for case in load_cases() if case["kind"] == "attack")
        trial = run_trial(case, ScriptedDemo(), "C0", 42)
        with tempfile.TemporaryDirectory() as tmp:
            write_report(Path(tmp), [trial], synthetic=False, model_identity_verified=False)
            events = [json.loads(line) for line in (Path(tmp) / "events.jsonl").read_text().splitlines()]
        self.assertTrue(all(event["model_identity_verified"] is False for event in events))


if __name__ == "__main__":
    unittest.main()
