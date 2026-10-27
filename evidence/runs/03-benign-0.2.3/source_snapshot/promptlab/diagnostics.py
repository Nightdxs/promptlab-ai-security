"""Diagnóstico de solo lectura. No instala software ni solicita inferencia."""
from __future__ import annotations

import platform
import shutil
import sys
from collections import Counter
from pathlib import Path

from .dataset import load_cases
from .ollama_backend import OllamaBackend


def diagnose(corpus: Path, model: str | None = None,
             base_url: str = "http://127.0.0.1:11434", timeout: float = 5) -> dict:
    report = {
        "python": platform.python_version(),
        "python_supported": sys.version_info >= (3, 10),
        "os": platform.system(), "architecture": platform.machine(),
        "ollama_cli_found": shutil.which("ollama") is not None,
        "corpus_valid": False, "model_metadata_verified": None,
        "inference_tested": False, "errors": [],
    }
    try:
        release = platform.freedesktop_os_release()
        report["distribution"] = release.get("PRETTY_NAME", release.get("NAME"))
    except (OSError, AttributeError):
        report["distribution"] = None
    try:
        report["disk_free_gib"] = round(shutil.disk_usage(Path.cwd()).free / 2**30, 1)
    except OSError:
        report["disk_free_gib"] = None
    report["ram_total_gib"] = None
    report["ram_available_gib"] = None
    try:
        memory = {line.split(":", 1)[0]: int(line.split()[1])
                  for line in Path("/proc/meminfo").read_text().splitlines()
                  if line.startswith(("MemTotal:", "MemAvailable:"))}
        for name, key in (("ram_total_gib", "MemTotal"), ("ram_available_gib", "MemAvailable")):
            if key in memory:
                report[name] = round(memory[key] / 2**20, 1)
    except (OSError, ValueError, IndexError):
        pass
    try:
        cases = load_cases(corpus)
        report.update(corpus_valid=True, cases=len(cases),
                      kinds=dict(Counter(case["kind"] for case in cases)))
    except (OSError, ValueError) as exc:
        report["errors"].append("Corpus: " + str(exc))
    report["ready_for_offline_demo"] = report["python_supported"] and report["corpus_valid"]
    if model is not None:
        report["model_metadata_verified"] = False
        try:
            report["model"] = OllamaBackend(model, base_url, timeout=timeout).describe()
            report["model_metadata_verified"] = True
        except (OSError, ValueError, RuntimeError) as exc:
            report["errors"].append("Ollama: " + str(exc))
    report["note"] = (
        "Sin --model no se realiza ninguna solicitud de red. Con --model solo se consultan "
        "metadatos en loopback; no se generan respuestas. Este diagnóstico no verifica "
        "aislamiento de red, configuración cloud del servidor, memoria suficiente ni utilidad del modelo."
    )
    return report
