"""Reproduce seis observaciones de la versión inicial sin Ollama ni inferencia."""
import argparse
import json
from pathlib import Path

from promptlab.core import run_trial
from promptlab.dataset import load_cases
from promptlab.ollama_backend import OllamaBackend


class Sequence:
    def __init__(self, responses):
        self.responses = iter(responses)

    def chat(self, *args):
        return next(self.responses)


def response(content="", tool=None, args=None, **extra):
    msg = {"role": "assistant", "content": content}
    if tool:
        msg["tool_calls"] = [{"function": {"name": tool, "arguments": args}}]
    return dict(message=msg, **extra)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expect-fixed", action="store_true")
    args = parser.parse_args()
    case = next(case for case in load_cases() if case["kind"] == "attack")
    results = []
    for name, reply, expected_status in [
        ("malformed_tool_calls", {"message": {"role": "assistant", "content": "", "tool_calls": {}}}, "backend_error"),
        ("truncated_generation", response(done=True, done_reason="length"), "generation_limit"),
        ("nonterminal_response", response(done=False), "backend_error"),
    ]:
        result = run_trial(case, Sequence([reply]), "C0", 42)
        results.append({"finding": name, "actual_status": result["status"],
                        "actual_attack_success": result["attack_success"],
                        "fixed": result["status"] == expected_status and result["attack_success"] is None})
    case = next(case for case in load_cases() if case["task"] == "mail")
    result = run_trial(case, Sequence([
        response(tool="enviar_correo", args={"destinatario": "ana@equipo.invalid", "asunto": "Resumen",
                 "cuerpo": "Aurora. 23 de diciembre. Ana Torres."}), response("Listo")]), "C0", 42)
    results.append({"finding": "mail_without_required_read", "actual_utility": result["legitimate_task_success"],
                    "fixed": result["legitimate_task_success"] is False})
    for key in ("temperature", "timeout"):
        try:
            OllamaBackend("x", **{key: float("nan")})
            accepted = True
        except ValueError:
            accepted = False
        results.append({"finding": "nonfinite_" + key, "accepted": accepted, "fixed": not accepted})
    text = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1 if args.expect_fixed and not all(item["fixed"] for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
