"""Embeddings locales con Ollama + EmbeddingGemma (los mismos del ACA 1).

La pregunta del usuario se vectoriza en el equipo con el mismo modelo y los
mismos prefijos de tarea con los que se indexó el corpus; solo el vector viaja
a Supabase.
"""
from __future__ import annotations

import time

import numpy as np
import requests


class OllamaEmbedder:
    def __init__(self, host: str, model: str, dim: int, timeout: int = 120):
        self.host = host.rstrip("/")
        self.model = model
        self.dim = dim
        self.timeout = timeout

    # ---------- estado ----------
    def health(self) -> tuple[bool, str]:
        try:
            tags = requests.get(f"{self.host}/api/tags", timeout=5).json()
        except requests.exceptions.RequestException:
            return False, "Ollama no responde. Abre la app de Ollama o ejecuta `ollama serve`."
        names = [m["name"] for m in tags.get("models", [])]
        if not any(n.split(":")[0] == self.model.split(":")[0] for n in names):
            return False, f"Falta el modelo `{self.model}`. Ejecuta `ollama pull {self.model}`."
        return True, f"{self.model} ({self.dim} d)"

    # ---------- vectorización ----------
    @staticmethod
    def _normalize(matrix) -> np.ndarray:
        arr = np.asarray(matrix, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return arr / norms

    def embed(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            last_exc: Exception | None = None
            for attempt in range(4):
                try:
                    r = requests.post(
                        f"{self.host}/api/embed",
                        json={"model": self.model, "input": batch, "truncate": True, "keep_alive": "10m"},
                        timeout=self.timeout,
                    )
                    r.raise_for_status()
                    vectors.extend(r.json()["embeddings"])
                    break
                except requests.exceptions.RequestException as exc:
                    last_exc = exc
                    time.sleep(2 ** attempt)
            else:
                raise RuntimeError(f"Ollama no respondió tras varios reintentos: {last_exc}")
        out = self._normalize(vectors)
        if out.shape[1] != self.dim:
            raise ValueError(f"El modelo devolvió {out.shape[1]} dimensiones y la tabla espera {self.dim}.")
        return out

    def embed_documents(self, records: list[dict]) -> np.ndarray:
        """Prefijo de documento de EmbeddingGemma: 'title: ... | text: ...'."""
        return self.embed([f"title: {r.get('title') or 'none'} | text: {r['content']}" for r in records])

    def embed_query(self, question: str) -> np.ndarray:
        """Prefijo de consulta de EmbeddingGemma (recuperación)."""
        return self.embed([f"task: search result | query: {question}"])[0]
