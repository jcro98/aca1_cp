"""Acceso a la base vectorial del ACA 1: Supabase (PostgreSQL + pgvector).

Tabla `rag_salud` con columna `vector(768)`, índice HNSW y distancia coseno.
"""
from __future__ import annotations

import hashlib
import time
from typing import Any

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def make_chunk_id(rec: dict) -> str:
    """Mismo hash SHA-1 que el notebook del ACA 1 -> upsert idempotente."""
    raw = f"{rec['source']}|{rec['metadata'].get('page')}|{rec['chunk_index']}|{rec['content']}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


class VectorStore:
    def __init__(self, database_url: str, table: str = "rag_salud"):
        if not database_url:
            raise ValueError("Falta DATABASE_URL en .env")
        if not table.replace("_", "").isalnum():
            raise ValueError("Nombre de tabla inválido")
        self.database_url = database_url
        self.table = table
        self._conn: psycopg.Connection | None = None

    # ---------- conexión con reconexión automática ----------
    def _connect(self) -> psycopg.Connection:
        # prepare_threshold=None -> compatible con el pooler de Supabase
        conn = psycopg.connect(self.database_url, prepare_threshold=None, autocommit=True, connect_timeout=10)
        conn.execute("set search_path = public, extensions")
        register_vector(conn)
        return conn

    @property
    def conn(self) -> psycopg.Connection:
        if self._conn is None or self._conn.closed:
            self._conn = self._connect()
        return self._conn

    def _run(self, fn, retries: int = 1):
        """Ejecuta fn(conn); si el pooler cerró la conexión, reconecta una vez."""
        for attempt in range(retries + 1):
            try:
                return fn(self.conn)
            except (psycopg.OperationalError, psycopg.InterfaceError):
                if self._conn is not None:
                    try:
                        self._conn.close()
                    except Exception:
                        pass
                self._conn = None
                if attempt == retries:
                    raise

    def _fetch(self, sql: str, params: Any = None) -> list[dict]:
        def fn(conn):
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
        return self._run(fn)

    def close(self) -> None:
        if self._conn is not None and not self._conn.closed:
            self._conn.close()

    # ---------- estado ----------
    def health(self) -> tuple[bool, str]:
        try:
            row = self._fetch(
                "select (select extversion from pg_extension where extname = 'vector') as v, "
                f"(select count(*) from public.{self.table}) as n"
            )[0]
            return True, f"pgvector {row['v']} · {row['n']} vectores"
        except Exception as exc:  # noqa: BLE001
            return False, f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}"

    def stats(self) -> dict:
        row = self._fetch(f"""
            select count(*) as vectores,
                   count(distinct source) as fuentes,
                   count(distinct doc_type) as tipos,
                   max(created_at) as ultima_carga,
                   pg_size_pretty(pg_total_relation_size('public.{self.table}')) as tamano,
                   (select extversion from pg_extension where extname = 'vector') as pgvector,
                   (select atttypmod from pg_attribute
                     where attrelid = 'public.{self.table}'::regclass and attname = 'embedding') as dim
            from public.{self.table}
        """)[0]
        idx = self._fetch("select indexname, indexdef from pg_indexes where tablename = %s", (self.table,))
        row["indices"] = idx
        return row

    def sources(self) -> list[dict]:
        return self._fetch(f"""
            select source, doc_type, count(*) as fragmentos,
                   sum(length(content)) as caracteres,
                   min(metadata->>'documento') as documento,
                   max(created_at) as cargado
            from public.{self.table}
            group by source, doc_type
            order by doc_type, source
        """)

    def chunks(self, source: str, limit: int = 500) -> list[dict]:
        return self._fetch(
            f"""select id, chunk_index, title, content, metadata, length(content) as caracteres
                from public.{self.table} where source = %s order by chunk_index limit %s""",
            (source, limit),
        )

    # ---------- búsqueda semántica ----------
    def search(self, qvec: np.ndarray, k: int = 5, doc_type: str | None = None) -> list[dict]:
        sql = f"""
            select id, source, doc_type, title, content, metadata,
                   1 - (embedding <=> %(q)s) as similarity
            from public.{self.table}
            where (%(dt)s::text is null or doc_type = %(dt)s)
            order by embedding <=> %(q)s
            limit %(k)s
        """
        return self._fetch(sql, {"q": np.asarray(qvec, dtype=np.float32), "dt": doc_type, "k": k})

    # ---------- gestión documental ----------
    def upsert(self, records: list[dict], embeddings: np.ndarray, batch_size: int = 100) -> int:
        sql = f"""
            insert into public.{self.table}
                (chunk_id, source, doc_type, chunk_index, title, content, metadata, embedding)
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (chunk_id) do update
               set title = excluded.title, content = excluded.content,
                   metadata = excluded.metadata, embedding = excluded.embedding
        """

        def fn(conn):
            for start in range(0, len(records), batch_size):
                rows = [
                    (make_chunk_id(r), r["source"], r["doc_type"], r["chunk_index"], r["title"],
                     r["content"], Jsonb(r["metadata"]), embeddings[start + i])
                    for i, r in enumerate(records[start:start + batch_size])
                ]
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.executemany(sql, rows)
            return len(records)

        return self._run(fn)

    def delete_source(self, source: str, keep_ids: list[str] | None = None) -> int:
        """Borra los fragmentos de una fuente (o solo los que no estén en keep_ids)."""
        def fn(conn):
            if keep_ids:
                cur = conn.execute(
                    f"delete from public.{self.table} where source = %s and not (chunk_id = any(%s))",
                    (source, keep_ids),
                )
            else:
                cur = conn.execute(f"delete from public.{self.table} where source = %s", (source,))
            return cur.rowcount
        return self._run(fn)

    def ping_latency_ms(self) -> float:
        t0 = time.perf_counter()
        self._fetch("select 1 as ok")
        return (time.perf_counter() - t0) * 1000
