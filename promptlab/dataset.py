from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path


DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / "data" / "cases_dev.jsonl"


def load_cases(path: Path = DEFAULT_CORPUS) -> list[dict]:
    cases = []
    seen = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        case = json.loads(line)
        if not isinstance(case, dict):
            raise ValueError(f"Caso no es un objeto, línea {number}")
        required = {"id", "kind", "split", "placement", "task", "user_task", "expected", "payload"}
        if not required <= case.keys():
            raise ValueError(f"Faltan campos, línea {number}")
        if not isinstance(case["id"], str) or not case["id"] or case["id"] in seen:
            raise ValueError(f"ID vacío o duplicado, línea {number}")
        if case["kind"] not in ("attack", "benign") or case["task"] not in ("summary", "lookup", "mail"):
            raise ValueError(f"Tipo de caso o tarea inválido, línea {number}")
        if case["placement"] not in ("none", "direct", "document", "database"):
            raise ValueError(f"Canal inválido, línea {number}")
        if not isinstance(case["split"], str) or not case["split"]:
            raise ValueError(f"Partición inválida, línea {number}")
        if any(not isinstance(case[key], str) for key in ("user_task", "payload")):
            raise ValueError(f"Texto inválido, línea {number}")
        if (not isinstance(case["expected"], list) or not case["expected"]
                or any(not isinstance(token, str) or not token for token in case["expected"])):
            raise ValueError(f"Criterios de utilidad inválidos, línea {number}")
        if case["kind"] == "attack" and (case.get("goal") not in ("exfiltration", "unauthorized_tool")
                                          or case["placement"] == "none" or not case["payload"]):
            raise ValueError(f"Objetivo de ataque inválido, línea {number}")
        if case["kind"] == "benign" and (case["placement"] != "none" or case["payload"]):
            raise ValueError(f"Caso benigno con inyección, línea {number}")
        if case["kind"] == "benign" and case.get("goal") is not None:
            raise ValueError(f"Caso benigno con objetivo de ataque, línea {number}")
        if ((case["placement"] == "database" and case["task"] != "lookup")
                or (case["placement"] == "document" and case["task"] not in ("summary", "mail"))):
            raise ValueError(f"Canal incompatible con los fixtures de la tarea, línea {number}")
        seen.add(case["id"])
        cases.append(case)
    if not cases:
        raise ValueError("El corpus está vacío")
    return cases


def select_cases(cases: list[dict], split: str, limit_per_kind: int | None = None) -> list[dict]:
    if limit_per_kind is not None and limit_per_kind < 1:
        raise ValueError("El límite debe ser positivo")
    buckets = {"attack": defaultdict(deque), "benign": defaultdict(deque)}
    for case in cases:
        if case["split"] == split:
            key = (case["placement"], case.get("goal")) if case["kind"] == "attack" else case["task"]
            buckets[case["kind"]][key].append(case)
    selected = []
    for kind, groups in buckets.items():
        count = 0
        while any(groups.values()) and (limit_per_kind is None or count < limit_per_kind):
            for queue in groups.values():
                if queue and (limit_per_kind is None or count < limit_per_kind):
                    selected.append(queue.popleft())
                    count += 1
    if not selected:
        raise ValueError("No hay casos para la partición solicitada")
    return selected
