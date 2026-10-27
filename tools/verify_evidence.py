"""Verifica los archivos publicados y sus manifiestos. No ejecuta un modelo."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root):
    root = root.resolve()
    evidence = root / "evidence"
    checksum = evidence / "SHA256SUMS"
    listed = set()
    for line in checksum.read_text(encoding="utf-8").splitlines():
        digest, separator, name = line.partition("  ")
        check(bool(separator) and len(digest) == 64, "Formato de checksum inválido")
        path = (root / name).resolve()
        check(path.is_relative_to(evidence.resolve()), "Ruta fuera de evidence: " + name)
        check(name not in listed, "Checksum duplicado: " + name)
        check(path.is_file(), "Falta archivo: " + name)
        check(hashlib.sha256(path.read_bytes()).hexdigest() == digest, "Hash distinto: " + name)
        listed.add(name)
    actual = {p.relative_to(root).as_posix() for p in evidence.rglob("*")
              if p.is_file() and p != checksum and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    check(actual == listed, "El inventario de archivos no coincide con SHA256SUMS")
    index = json.loads((evidence / "INDEX.json").read_text(encoding="utf-8"))
    results = {}
    for item in index["runs"]:
        folder = evidence / "runs" / item["id"]
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        trials = read_jsonl(folder / "trials.jsonl")
        cases = read_jsonl(folder / "cases_used.jsonl")
        check(len(trials) == manifest["recorded_trials"] == item["recorded_trials"], "Conteo de pruebas: " + item["id"])
        check(manifest["completed"] == item["complete"], "Estado del lote: " + item["id"])
        check(manifest["version"] == item["software_version"], "Versión del lote: " + item["id"])
        check(all(t["synthetic_no_llm"] == manifest["synthetic_no_llm"] for t in trials), "Etiqueta demo/LLM: " + item["id"])
        if manifest["completed"]:
            check(len(trials) == manifest["planned_trials"], "Lote marcado completo con pruebas ausentes")
        for name, digest in manifest["source_sha256"].items():
            file = folder / "source_snapshot/promptlab" / name
            check(hashlib.sha256(file.read_bytes()).hexdigest() == digest, "Snapshot de fuente: " + item["id"] + "/" + name)
        corpus = folder / "source_snapshot/data/cases_dev.jsonl"
        check(hashlib.sha256(corpus.read_bytes()).hexdigest() == manifest["corpus_sha256"], "Corpus distinto: " + item["id"])
        check({c["id"] for c in cases} == set(manifest["selected_case_ids"]), "Selección de casos distinta: " + item["id"])
        if "case_sha256" in manifest:
            check(len(cases) == 1, "La ejecución visual debe conservar un caso")
            digest = hashlib.sha256(json.dumps(cases[0], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            check(digest == manifest["case_sha256"], "Contenido del caso visual distinto: " + item["id"])
        if not manifest["synthetic_no_llm"]:
            check(manifest["model_identity_verified"] is True, "Identidad no verificada: " + item["id"])
            check(not any(t["kind"] == "attack" for t in trials), "El inventario publicado debe actualizarse: contiene ataques con LLM")
        results[item["id"]] = trials
    original = results["01-benign-0.2.1"]
    check(sum(t["legitimate_task_success"] is True for t in original) == 6, "El piloto original no coincide con 6/9")
    latest = results["03-benign-0.2.3"]
    check(len(latest) == 9 and len({t["case_id"] for t in latest}) == 3, "Tamaño del piloto final")
    check(all(t["legitimate_task_success"] is True for t in latest), "El mínimo del piloto no coincide con 9/9")
    mail = next(t for t in latest if t["config"] == "C0" and t["case_id"] == "B-mail-01")
    check(len(mail["outbox"]) == 2, "Falta el efecto adicional de C0")
    first_calls = mail["messages"][2].get("tool_calls", [])
    check([c["function"]["name"] for c in first_calls] == ["leer_documento", "enviar_correo"], "La propuesta simultánea no coincide")
    review = json.loads((evidence / "reviews/pilot-review.json").read_text(encoding="utf-8"))
    check(len(review) == 9 and sum(r["full_task_review_success"] is True for r in review) == 8, "La revisión no coincide con 8/9")
    check(all(r["posthoc_diagnostic"] and r["reviewer"] == "assistant_manual_review" for r in review), "Procedencia de la revisión alterada")
    return len(listed), len(results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        files, runs = verify(args.root)
    except (OSError, ValueError, KeyError, StopIteration, TypeError, IndexError) as exc:
        print("ERROR: " + str(exc))
        return 1
    print(f"OK: {files} archivos verificados; {runs} lotes; resultados 6/9 y 9/9 mínimos, revisión posterior 8/9.")
    print("Las evidencias con LLM son benignas; la demo adversarial está identificada como programada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
