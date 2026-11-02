-- ACA 1 · Computación en la Nube · Pilar Salud · Supabase + pgvector
-- Dimensión del vector = 768 (EmbeddingGemma vía Ollama). El notebook ejecuta este mismo archivo.
set search_path = public, extensions;

create schema if not exists extensions;   -- ya existe en Supabase; se deja por portabilidad
create extension if not exists vector with schema extensions;

create table if not exists public.rag_salud (
  id          bigint generated always as identity primary key,
  chunk_id    text unique not null,          -- hash SHA-1 determinista -> upsert idempotente
  source      text not null,                 -- archivo o dataset de origen
  doc_type    text not null,                 -- documento | dataset_variable | dataset_resumen
  chunk_index int,
  title       text,                          -- documento - sección
  content     text not null,
  metadata    jsonb not null default '{}'::jsonb,
  embedding   vector(768) not null,
  created_at  timestamptz not null default now()
);

-- Métrica de distancia: coseno (vectores normalizados)
create index if not exists rag_salud_embedding_hnsw
  on public.rag_salud using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

create index if not exists rag_salud_doc_type_idx on public.rag_salud (doc_type);

-- Seguridad: RLS activo. El notebook se conecta con el rol postgres (que omite RLS);
-- la API pública (anon/authenticated) no tiene acceso mientras no se creen políticas.
alter table public.rag_salud enable row level security;

-- Búsqueda Top-k reutilizable como RPC desde una API o un agente RAG
create or replace function public.match_salud(
  query_embedding vector(768),
  match_count int default 5,
  filter_doc_type text default null
)
returns table (
  id bigint, source text, doc_type text, title text,
  content text, metadata jsonb, similarity float
)
language sql stable
set search_path = public, extensions
as $$
  select c.id, c.source, c.doc_type, c.title, c.content, c.metadata,
         1 - (c.embedding <=> query_embedding) as similarity
  from public.rag_salud c
  where filter_doc_type is null or c.doc_type = filter_doc_type
  order by c.embedding <=> query_embedding
  limit match_count;
$$;
