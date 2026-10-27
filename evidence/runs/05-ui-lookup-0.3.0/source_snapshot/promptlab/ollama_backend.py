from __future__ import annotations

import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request


def reject_nonfinite(value: str):
    raise ValueError("Valor JSON no finito: " + value)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OllamaBackend:
    def __init__(self, model: str, base_url: str = "http://127.0.0.1:11434",
                 temperature: float = 0.0, num_predict: int = 800,
                 num_ctx: int = 8192, timeout: float = 180):
        url = urllib.parse.urlsplit(base_url)
        if (url.scheme != "http" or url.hostname not in ("localhost", "127.0.0.1", "::1")
                or url.username or url.password or url.path not in ("", "/")
                or url.query or url.fragment):
            raise ValueError("Solo se admite un servidor Ollama HTTP en loopback, sin ruta ni credenciales")
        try:
            port = url.port
        except ValueError as exc:
            raise ValueError("Puerto de Ollama inválido") from exc
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("Puerto de Ollama inválido")
        if (not isinstance(model, str) or not model.strip() or model != model.strip()
                or type(num_predict) is not int or num_predict < 1
                or type(num_ctx) is not int or num_ctx < 256
                or type(temperature) not in (int, float) or not math.isfinite(temperature) or temperature < 0
                or type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0):
            raise ValueError("Parámetros del modelo inválidos")
        if re.search(r"(?:[:\-])cloud$", model, re.IGNORECASE):
            raise ValueError("Este laboratorio solo admite modelos locales; nombre cloud rechazado")
        self.model = model
        # Evita que un nombre localhost alterado se resuelva fuera de loopback.
        self.base_url = ("http://127.0.0.1" + (":" + str(port) if port else "")) if url.hostname == "localhost" else base_url.rstrip("/")
        self.temperature = temperature
        self.num_predict = num_predict
        self.num_ctx = num_ctx
        self.timeout = timeout
        self._verified_model = None
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def _request(self, path: str, data: dict | None = None) -> dict:
        payload = json.dumps(data, ensure_ascii=False, allow_nan=False).encode() if data is not None else None
        request = urllib.request.Request(self.base_url + path, data=payload,
                                         headers={"Content-Type": "application/json"},
                                         method="POST" if data is not None else "GET")
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read(16 * 1024 * 1024 + 1)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Ollama devolvió HTTP {exc.code}; revisa modelo y compatibilidad de herramientas") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("No se pudo completar la solicitud al servidor local Ollama") from exc
        if len(raw) > 16 * 1024 * 1024:
            raise RuntimeError("Respuesta de Ollama demasiado grande")
        value = json.loads(raw, parse_constant=reject_nonfinite)
        if not isinstance(value, dict) or "error" in value:
            raise RuntimeError("Respuesta de Ollama inválida o con error")
        return value

    def describe(self) -> dict:
        models = self._request("/api/tags").get("models", [])
        if not isinstance(models, list) or any(not isinstance(item, dict) for item in models):
            raise ValueError("Listado de modelos inválido")
        names = [self.model] if ":" in self.model else [self.model, self.model + ":latest"]
        match = next((item for item in models if item.get("name") in names), None)
        if not match or not match.get("digest"):
            raise ValueError("Modelo no encontrado localmente con digest; usa su nombre exacto de ollama list")
        if match.get("remote_host") or match.get("remote_model"):
            raise ValueError("El modelo declara un backend remoto; no se enviaron tareas")
        shown = self._request("/api/show", {"model": self.model})
        if shown.get("remote_host") or shown.get("remote_model"):
            raise ValueError("El alias remite a un modelo remoto; no se enviaron tareas")
        capabilities = shown.get("capabilities", [])
        if not isinstance(capabilities, list) or "tools" not in capabilities:
            raise ValueError("El modelo no declara soporte de herramientas en /api/show")
        server = self._request("/api/version")
        if not isinstance(server.get("version"), str) or not server["version"]:
            raise ValueError("Versión del servidor no verificable")
        self._verified_model = match["name"]
        return {"requested_model": self.model, "local_model": match,
                "model_capabilities": capabilities, "model_details": shown.get("details", {}),
                "server": server, "base_url": self.base_url,
                "temperature": self.temperature, "num_predict": self.num_predict,
                "num_ctx": self.num_ctx, "timeout_seconds": self.timeout}

    def chat(self, messages: list[dict], tools: list[dict], seed: int) -> dict:
        if self._verified_model is None:
            self.describe()
        response = self._request("/api/chat", {
            "model": self.model, "messages": messages, "tools": tools,
            "stream": False, "options": {
                "temperature": self.temperature, "seed": seed,
                "num_predict": self.num_predict, "num_ctx": self.num_ctx,
            },
        })
        if response.get("remote_host") or response.get("remote_model"):
            raise RuntimeError("Respuesta de inferencia remota rechazada; revisa la configuración del servidor")
        if response.get("model") not in (self.model, self._verified_model):
            raise RuntimeError("La respuesta no corresponde al modelo solicitado")
        if response.get("done") is not True:
            raise RuntimeError("Respuesta no terminal para una solicitud no streaming")
        return response
