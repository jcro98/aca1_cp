"""Configuración central del sistema RAG (ACA 2).

Todas las credenciales se leen de variables de entorno (`.env` en la raíz del
proyecto) o, si la app se despliega en Streamlit Community Cloud, de
`st.secrets`. Nunca se escriben claves en el código.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "data" / "corpus"
load_dotenv(ROOT / ".env")


def get_secret(name: str, default: str | None = None) -> str | None:
    """Busca un secreto en: variables de entorno -> st.secrets -> Colab Secrets."""
    value = os.environ.get(name)
    if value:
        return value
    try:  # Streamlit (solo si existe .streamlit/secrets.toml)
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    try:  # Google Colab
        from google.colab import userdata  # type: ignore

        return userdata.get(name)
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    # Base vectorial (ACA 1)
    database_url: str | None
    table: str
    # Embeddings locales (mismo modelo con el que se indexó en el ACA 1)
    ollama_host: str
    embed_model: str
    embed_dim: int
    # LLM en la nube
    gemini_api_key: str | None
    gemini_model: str
    # Hiperparámetros por defecto (se pueden ajustar en la barra lateral)
    top_k: int = 5
    sim_threshold: float = 0.70
    temperature: float = 0.2
    top_p: float = 0.9
    max_output_tokens: int = 1024
    history_turns: int = 6
    # Chunking idéntico al ACA 1 (para que los chunk_id coincidan)
    chunk_size: int = 800
    chunk_overlap: int = 120


def load_settings() -> Settings:
    return Settings(
        database_url=get_secret("DATABASE_URL"),
        table=get_secret("RAG_TABLE", "rag_salud"),
        ollama_host=(get_secret("OLLAMA_HOST", "http://localhost:11434") or "").rstrip("/"),
        embed_model=get_secret("EMBED_MODEL", "embeddinggemma"),
        embed_dim=int(get_secret("EMBED_DIM", "768")),
        gemini_api_key=get_secret("GEMINI_API_KEY") or get_secret("GOOGLE_API_KEY"),
        gemini_model=get_secret("GEMINI_MODEL", "gemini-2.5-flash"),
        top_k=int(get_secret("TOP_K", "5")),
        sim_threshold=float(get_secret("SIM_THRESHOLD", "0.70")),
        temperature=float(get_secret("TEMPERATURE", "0.2")),
    )
