from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .core import CONFIGS, ScriptedDemo, run_trial
from .dataset import DEFAULT_CORPUS, load_cases, select_cases
from .diagnostics import diagnose
from .ollama_backend import OllamaBackend
from .reporting import write_report


def save_execution(args, cases: list[dict], backend, synthetic: bool, metadata: dict):
    folder = Path(args.output) / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                                + "_" + ("DEMO_" if synthetic else "OLLAMA_") + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    config_list = list(dict.fromkeys(args.configs))
    jobs = [(case, config, args.seed + repetition) for case in cases
            for repetition in range(args.repeats) for config in config_list]
    # Orden aleatorio determinista para reducir confusión por calentamiento/carga.
    random.Random(args.seed).shuffle(jobs)
    source_root = Path(__file__).resolve().parent
    source_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted(source_root.glob("*.py"))}
    manifest = {
        "version": __version__, "started_utc": datetime.now(timezone.utc).isoformat(),
        "synthetic_no_llm": synthetic, "backend": metadata, "python": sys.version,
        "platform": platform.platform(), "configs": config_list,
        "config_definitions": {name: CONFIGS[name] for name in config_list},
        "corpus_sha256": hashlib.sha256(Path(args.corpus).read_bytes()).hexdigest(),
        "source_sha256": source_hashes, "selected_case_ids": [case["id"] for case in cases],
        "split": args.split, "seed": args.seed, "repeats": args.repeats,
        "case_kind": getattr(args, "kind", "all"),
        "max_turns": args.max_turns, "max_tool_calls": args.max_calls,
        "planned_trials": len(jobs), "completed": False,
        "independence_note": "Repeticiones agrupadas por caso; no son observaciones independientes.",
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    # Se preservan exactamente los casos utilizados para reproducir el lote.
    (folder / "cases_used.jsonl").write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases), encoding="utf-8")
    print("SIN LLM: secuencia programada, no resultados experimentales." if synthetic else "Evaluación local iniciada.")
    print(f"{len(jobs)} pruebas; salida: {folder}", flush=True)
    trials = []
    interrupted = False
    try:
        with (folder / "trials.jsonl").open("w", encoding="utf-8") as stream:
            for index, (case, config, seed) in enumerate(jobs, 1):
                trial = run_trial(case, backend, config, seed, args.max_turns, args.max_calls)
                trial["synthetic_no_llm"] = synthetic
                stream.write(json.dumps(trial, ensure_ascii=False) + "\n")
                stream.flush()
                trials.append(trial)
                print(f"[{index}/{len(jobs)}] {case['id']} {config}: {trial['status']}", flush=True)
    except KeyboardInterrupt:
        interrupted = True
        print("Interrumpido; se conserva el registro parcial.", file=sys.stderr)
    manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["recorded_trials"] = len(trials)
    manifest["interrupted"] = interrupted
    manifest["completed"] = len(trials) == len(jobs)
    if not synthetic:
        try:
            after = backend.describe()
            manifest["backend_after"] = after
            manifest["model_digest_unchanged"] = metadata["local_model"]["digest"] == after["local_model"]["digest"]
            manifest["model_identity_verified"] = manifest["model_digest_unchanged"] and all(
                metadata.get(key) == after.get(key) for key in
                ("requested_model", "server", "model_capabilities", "model_details"))
        except Exception as exc:
            manifest["model_digest_unchanged"] = None
            manifest["model_identity_verified"] = None
            manifest["postcheck_error"] = str(exc)
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(folder, trials, synthetic, planned_trials=len(jobs),
                 model_identity_verified=manifest.get("model_identity_verified"))
    print("Informe: " + str(folder / "SUMMARY.md"))
    backend_failures = any(trial["status"] != "completed" for trial in trials)
    invalid_identity = not synthetic and manifest.get("model_identity_verified") is not True
    return 2 if interrupted or backend_failures or invalid_identity else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="PromptLab: laboratorio local con datos ficticios")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="Valida el corpus sin ejecutar un modelo")
    inspect.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    doctor = sub.add_parser("doctor", help="Diagnóstico de entorno y metadatos, sin inferencia")
    doctor.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    doctor.add_argument("--model", help="Opcional: consulta solo metadatos del modelo local")
    doctor.add_argument("--base-url", default="http://127.0.0.1:11434")
    doctor.add_argument("--timeout", type=float, default=5)
    for name in ("demo", "run"):
        command = sub.add_parser(name, help="Prueba programada sin LLM" if name == "demo" else "Ejecuta un modelo Ollama local")
        command.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
        command.add_argument("--output", default="results")
        command.add_argument("--configs", nargs="+", choices=list(CONFIGS), default=["C0", "C2", "C2P"])
        command.add_argument("--seed", type=int, default=42)
        command.add_argument("--repeats", type=int, default=1)
        command.add_argument("--split", default="dev")
        command.add_argument("--limit-per-kind", type=int)
        command.add_argument("--max-turns", type=int, default=10)
        command.add_argument("--max-calls", type=int, default=16)
        if name == "run":
            command.add_argument("--kind", choices=("all", "benign", "attack"), default="all",
                                 help="Permite comprobar tareas legítimas antes de evaluar ataques")
            command.add_argument("--model", required=True, help="Nombre exacto de un modelo local con soporte de herramientas")
            command.add_argument("--base-url", default="http://127.0.0.1:11434")
            command.add_argument("--temperature", type=float, default=0.0)
            command.add_argument("--num-predict", type=int, default=800)
            command.add_argument("--num-ctx", type=int, default=8192)
            command.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            report = diagnose(args.corpus, args.model, args.base_url, args.timeout)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["ready_for_offline_demo"] and not report["errors"] else 2
        cases = load_cases(args.corpus)
        if args.command == "inspect":
            print(json.dumps({"cases": len(cases), "kinds": dict(Counter(case["kind"] for case in cases)),
                              "channels": dict(Counter(case["placement"] for case in cases)),
                              "splits": dict(Counter(case["split"] for case in cases))}, ensure_ascii=False, indent=2))
            return 0
        if args.repeats < 1 or args.max_turns < 1 or args.max_calls < 1:
            raise ValueError("Repeticiones y presupuestos deben ser positivos")
        if getattr(args, "kind", "all") != "all":
            cases = [case for case in cases if case["kind"] == args.kind]
        cases = select_cases(cases, args.split, args.limit_per_kind)
        if args.command == "demo":
            # Una sola escena para demostrar el control, nunca el corpus completo.
            cases = [next(case for case in cases if case["kind"] == "attack" and case["goal"] == "exfiltration")]
            return save_execution(args, cases, ScriptedDemo(), True,
                                  {"type": "scripted_demo", "description": "No es un modelo de lenguaje"})
        backend = OllamaBackend(args.model, args.base_url, args.temperature,
                                args.num_predict, args.num_ctx, args.timeout)
        return save_execution(args, cases, backend, False, backend.describe())
    except (ValueError, OSError, RuntimeError, StopIteration) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
