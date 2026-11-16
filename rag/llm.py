"""Cliente del LLM en la nube: Google Gemini API (SDK oficial `google-genai`)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterator

from google import genai
from google.genai import errors, types


@dataclass
class GenParams:
    temperature: float = 0.2      # baja: respuestas factuales y reproducibles
    top_p: float = 0.9            # núcleo de probabilidad; recorta tokens improbables
    max_output_tokens: int = 1024  # suficiente para una respuesta clínica con viñetas y citas


@dataclass
class Usage:
    prompt_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    extra: dict = field(default_factory=dict)


def _usage_from(resp) -> Usage:
    um = getattr(resp, "usage_metadata", None)
    if not um:
        return Usage()
    return Usage(
        prompt_tokens=um.prompt_token_count or 0,
        output_tokens=um.candidates_token_count or 0,
        total_tokens=um.total_token_count or 0,
    )


def friendly_error(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    if code == 429:
        return "Se alcanzó la cuota gratuita de Gemini (HTTP 429). Espera un minuto o cambia a un modelo «flash-lite»."
    if code in (400, 401, 403):
        return f"Gemini rechazó la petición (HTTP {code}). Revisa GEMINI_API_KEY y el nombre del modelo."
    if code == 404:
        return "El modelo configurado no existe para esta API key. Elige otro en la barra lateral."
    return f"Error al llamar a Gemini: {type(exc).__name__}: {str(exc)[:200]}"


class GeminiLLM:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("Falta GEMINI_API_KEY en .env")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def list_models(self) -> list[str]:
        """Modelos de la API key que soportan generateContent (para el selector de la UI)."""
        names = []
        for m in self.client.models.list():
            actions = getattr(m, "supported_actions", None) or []
            name = (m.name or "").removeprefix("models/")
            if "generateContent" in actions and name.startswith("gemini") and "tts" not in name \
                    and "image" not in name and "embedding" not in name:
                names.append(name)
        return sorted(set(names))

    def _config(self, system: str | None, p: GenParams) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=system,
            temperature=p.temperature,
            top_p=p.top_p,
            max_output_tokens=p.max_output_tokens,
        )

    def generate(self, contents, system: str | None = None, params: GenParams | None = None,
                 retries: int = 2) -> tuple[str, Usage]:
        params = params or GenParams()
        for attempt in range(retries + 1):
            try:
                resp = self.client.models.generate_content(
                    model=self.model, contents=contents, config=self._config(system, params))
                return (resp.text or "").strip(), _usage_from(resp)
            except errors.APIError as exc:
                if getattr(exc, "code", None) in (429, 500, 503) and attempt < retries:
                    time.sleep(2 * (attempt + 1) ** 2)
                    continue
                raise

    def stream(self, contents, system: str | None = None, params: GenParams | None = None,
               usage_out: Usage | None = None) -> Iterator[str]:
        """Genera la respuesta token a token (st.write_stream) y llena usage_out al final."""
        params = params or GenParams()
        last = None
        for chunk in self.client.models.generate_content_stream(
                model=self.model, contents=contents, config=self._config(system, params)):
            last = chunk
            if chunk.text:
                yield chunk.text
        if usage_out is not None and last is not None:
            u = _usage_from(last)
            usage_out.prompt_tokens, usage_out.output_tokens, usage_out.total_tokens = (
                u.prompt_tokens, u.output_tokens, u.total_tokens)
