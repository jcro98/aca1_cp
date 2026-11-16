"""Ingesta de documentos nuevos desde la interfaz (.md, .txt, .pdf).

Replica exactamente el pipeline del notebook del ACA 1 (secciones '## ',
PDF por página, RecursiveCharacterTextSplitter 800/120, mismos metadatos),
de modo que un documento cargado desde la app produce los mismos chunk_id que
si se hubiera indexado desde el notebook.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

ALLOWED_EXT = {".md", ".txt", ".pdf"}


def make_splitter(size: int = 800, overlap: int = 120) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
    )


def split_markdown_sections(text: str) -> tuple[str | None, list[tuple[str, str]]]:
    doc_title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), None)
    parts = re.split(r"\n(?=## )", text)
    sections = []
    for part in parts:
        lines = part.strip().splitlines()
        if not lines:
            continue
        if lines[0].startswith("## "):
            sections.append((lines[0][3:].strip(), "\n".join(lines[1:]).strip()))
        else:
            body = "\n".join(l for l in lines if not l.startswith("# ")).strip()
            if body:
                sections.append(("Introducción", body))
    return doc_title, sections


def load_file(filename: str, data: bytes) -> list[dict]:
    """Devuelve [{source, doc_title, section, page, text}] para un archivo."""
    path = Path(filename)
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXT:
        raise ValueError(f"Formato no soportado: {ext}. Usa .md, .txt o .pdf")
    docs = []
    if ext in (".md", ".txt"):
        doc_title, sections = split_markdown_sections(data.decode("utf-8", errors="replace"))
        for sec_title, body in sections:
            docs.append({"source": path.name, "doc_title": doc_title or path.stem,
                         "section": sec_title, "page": None, "text": body})
    else:
        for i, page in enumerate(PdfReader(io.BytesIO(data)).pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                docs.append({"source": path.name, "doc_title": path.stem,
                             "section": f"Página {i}", "page": i, "text": text})
    return docs


def chunk_docs(docs: list[dict], size: int = 800, overlap: int = 120) -> list[dict]:
    splitter = make_splitter(size, overlap)
    records, counters = [], {}
    for d in docs:
        for text in splitter.split_text(d["text"]):
            idx = counters.get(d["source"], 0)
            counters[d["source"]] = idx + 1
            records.append({
                "source": d["source"], "doc_type": "documento", "chunk_index": idx,
                "title": f"{d['doc_title']} - {d['section']}", "content": text,
                "metadata": {"pilar": "salud", "documento": d["doc_title"], "seccion": d["section"],
                             "page": d["page"], "chunk_size": size, "chunk_overlap": overlap},
            })
    return records
