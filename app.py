"""ACA 2 · Computación en la Nube — Chatbot RAG clínico con Gemini + Supabase pgvector.

Ejecutar:  streamlit run app.py
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from rag.config import CORPUS_DIR, load_settings
from rag.embeddings import OllamaEmbedder
from rag.evaluation import TEST_CASES, run_evaluation, summarize
from rag.ingest import ALLOWED_EXT, chunk_docs, load_file
from rag.llm import GeminiLLM, GenParams, friendly_error
from rag.pipeline import SYSTEM_PROMPT, RAGPipeline, build_user_message
from rag.vectorstore import VectorStore, make_chunk_id

st.set_page_config(page_title="Asistente Clínico RAG · ACA 2", page_icon="🩺", layout="wide")

DOC_TYPES = {"Todos": None, "Documentos (guías y protocolos)": "documento",
             "Diccionario de variables (datasets)": "dataset_variable",
             "Resúmenes estadísticos (datasets)": "dataset_resumen"}
EXAMPLES = [
    "¿Qué cifras de presión arterial se consideran hipertensión?",
    "¿Qué conducta se recomienda ante un resultado BI-RADS 4?",
    "¿Qué porcentaje de pacientes asintomáticos tiene enfermedad coronaria en los datos?",
    "¿Qué debo hacer si me pincho con una aguja usada en una biopsia?",
]

# --------------------------------------------------------------------------------------
# Recursos compartidos (se crean una sola vez por sesión del servidor)
# --------------------------------------------------------------------------------------
S = load_settings()


@st.cache_resource(show_spinner=False)
def get_store() -> VectorStore:
    return VectorStore(S.database_url, S.table)


@st.cache_resource(show_spinner=False)
def get_embedder() -> OllamaEmbedder:
    return OllamaEmbedder(S.ollama_host, S.embed_model, S.embed_dim)


@st.cache_resource(show_spinner=False)
def get_llm(model: str) -> GeminiLLM | None:
    return GeminiLLM(S.gemini_api_key, model) if S.gemini_api_key else None


@st.cache_data(ttl=3600, show_spinner=False)
def available_models() -> list[str]:
    try:
        return get_llm(S.gemini_model).list_models()
    except Exception:  # noqa: BLE001
        return []


@st.cache_data(ttl=30, show_spinner=False)
def health() -> dict:
    return {"supabase": get_store().health(), "ollama": get_embedder().health()}


@st.cache_data(ttl=60, show_spinner=False)
def index_stats() -> tuple[dict, list[dict]]:
    store = get_store()
    return store.stats(), store.sources()


def short_title(h: dict) -> str:
    return (h.get("title") or h["source"]).split(" - ")[-1]


# --------------------------------------------------------------------------------------
# Verificación inicial
# --------------------------------------------------------------------------------------
if not S.database_url:
    st.error("Falta **DATABASE_URL** en el archivo `.env` (cadena del *Session pooler* de Supabase).")
    st.code("cp .env.example .env   # y completa DATABASE_URL y GEMINI_API_KEY", language="bash")
    st.stop()

st.session_state.setdefault("messages", [])
st.session_state.setdefault("eval_df", None)

# --------------------------------------------------------------------------------------
# Barra lateral: estado de servicios e hiperparámetros
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🩺 Asistente Clínico RAG")
    st.caption("ACA 2 · Computación en la Nube · CUN")

    st.markdown("#### Estado de servicios")
    hs = health()
    for label, (ok, msg) in (("Supabase pgvector", hs["supabase"]), ("Ollama (embeddings)", hs["ollama"])):
        (st.success if ok else st.error)(f"**{label}** · {msg}", icon="✅" if ok else "⚠️")
    if S.gemini_api_key:
        st.success("**Gemini API** · clave cargada desde el entorno", icon="✅")
    else:
        st.error("**Gemini API** · falta GEMINI_API_KEY en .env", icon="⚠️")
    if st.button("↻ Revisar de nuevo", use_container_width=True):
        health.clear()
        index_stats.clear()
        st.rerun()

    st.markdown("#### Modelo de lenguaje")
    models = available_models() or [S.gemini_model]
    if S.gemini_model not in models:
        models = [S.gemini_model] + models
    model = st.selectbox("Modelo Gemini", models, index=models.index(S.gemini_model),
                         help="Lista obtenida de la API con tu clave (solo modelos con generateContent).")
    temperature = st.slider("Temperatura", 0.0, 1.0, S.temperature, 0.05,
                            help="Baja = respuestas más deterministas y apegadas al contexto.")
    top_p = st.slider("Top-p", 0.1, 1.0, S.top_p, 0.05)
    max_tokens = st.slider("Máx. tokens de salida", 256, 4096, S.max_output_tokens, 128)

    st.markdown("#### Recuperación")
    top_k = st.slider("Top-k fragmentos", 1, 10, S.top_k)
    threshold = st.slider("Umbral de similitud", 0.0, 0.95, S.sim_threshold, 0.01,
                          help="Si el mejor fragmento no lo supera, el asistente no llama al LLM y responde "
                               "que no tiene información (ACA 1: dominio ≈ 0.81 vs fuera de dominio ≈ 0.60).")
    doc_filter = DOC_TYPES[st.selectbox("Buscar en", list(DOC_TYPES))]
    rewrite = st.toggle("Reescribir preguntas de seguimiento", value=True,
                        help="Usa Gemini para convertir «¿y en mujeres?» en una pregunta completa antes de buscar.")
    show_debug = st.toggle("Mostrar detalles técnicos", value=False)

    params = GenParams(temperature=temperature, top_p=top_p, max_output_tokens=max_tokens)

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("🗑️ Nuevo chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    def conversation_md() -> str:
        lines = [f"# Conversación · Asistente Clínico RAG\n\n_{datetime.now():%Y-%m-%d %H:%M}_ · modelo `{model}`\n"]
        for m in st.session_state.messages:
            lines.append(f"**{'Usuario' if m['role'] == 'user' else 'Asistente'}:** {m['content']}\n")
            for i, h in enumerate(m.get("hits", []), start=1):
                lines.append(f"> [{i}] {h['source']} · {short_title(h)} (sim {h['similarity']:.3f})")
            lines.append("")
        return "\n".join(lines)

    c2.download_button("⬇️ Exportar", conversation_md(), file_name="conversacion_rag.md",
                       use_container_width=True, disabled=not st.session_state.messages)

store, embedder, llm = get_store(), get_embedder(), get_llm(model)
pipe = RAGPipeline(store, embedder, llm)

tab_chat, tab_docs, tab_search, tab_eval, tab_arch = st.tabs(
    ["💬 Chat", "📚 Gestión documental", "🔎 Consulta vectorial", "🧪 Evaluación", "🧭 Arquitectura"])


# --------------------------------------------------------------------------------------
# Componentes de visualización
# --------------------------------------------------------------------------------------
def render_sources(msg: dict, key: str) -> None:
    hits, cited = msg.get("hits") or [], set(msg.get("cited") or [])
    if not hits:
        return
    label = f"📎 Fuentes · {len(cited)} citadas de {len(hits)} recuperadas" if not msg.get("refused") \
        else f"📎 Fragmentos más cercanos (ninguno supera el umbral {msg.get('threshold', threshold):.2f})"
    with st.expander(label, expanded=False):
        for i, h in enumerate(hits, start=1):
            meta = h.get("metadata") or {}
            badge = "🟢 **citado**" if i in cited else "⚪ no citado"
            page = f" · pág. {meta['page']}" if meta.get("page") else ""
            st.markdown(f"**[{i}] {short_title(h)}** — `{h['source']}`{page} · {h['doc_type']} · {badge}")
            st.progress(min(max(float(h["similarity"]), 0.0), 1.0), text=f"similitud coseno {h['similarity']:.3f}")
            st.caption(" ".join(h["content"].split())[:600] + ("…" if len(h["content"]) > 600 else ""))
        if show_debug and msg.get("timings"):
            t = msg["timings"]
            st.markdown("---")
            st.caption(
                "⏱ " + " · ".join(f"{k.replace('_ms', '')}: {v:.0f} ms" for k, v in t.items())
                + (f" · tokens: {msg['usage']['total_tokens']}" if msg.get("usage") else "")
                + (f" · pregunta usada para buscar: «{msg['standalone']}»" if msg.get("standalone") else ""))


# --------------------------------------------------------------------------------------
# 1) CHAT
# --------------------------------------------------------------------------------------
with tab_chat:
    st.markdown("### Chat clínico con evidencia documental")
    st.caption("Las respuestas se generan con Gemini **solo** a partir de los fragmentos recuperados de Supabase "
               "y citan la fuente con [n]. Herramienta académica: no reemplaza el criterio médico.")

    chat_box = st.container()
    welcome = chat_box.empty()
    if not st.session_state.messages and "pending" not in st.session_state:
        with welcome.container():
            st.info("Prueba con una de estas preguntas o escribe la tuya abajo.")
            cols = st.columns(2)
            for i, ex in enumerate(EXAMPLES):
                if cols[i % 2].button(ex, key=f"ex{i}", use_container_width=True):
                    st.session_state.pending = ex
                    st.rerun()
    with chat_box:
        for idx, m in enumerate(st.session_state.messages):
            with st.chat_message(m["role"], avatar="🧑‍⚕️" if m["role"] == "user" else "🩺"):
                st.markdown(m["content"])
                if m["role"] == "assistant":
                    render_sources(m, key=f"m{idx}")

    prompt = st.chat_input("Escribe tu pregunta clínica…", disabled=llm is None)
    prompt = prompt or st.session_state.pop("pending", None)

    if prompt:
        welcome.empty()
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_box:
            with st.chat_message("user", avatar="🧑‍⚕️"):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar="🩺"):
                msg = {"role": "assistant", "threshold": threshold}
                try:
                    with st.spinner("Buscando en la base vectorial…"):
                        turn = pipe.prepare(prompt, history, k=top_k, threshold=threshold, doc_type=doc_filter,
                                            rewrite=rewrite, history_turns=S.history_turns)
                    if turn.refused:
                        st.markdown(turn.answer)
                        pipe.finalize(turn, turn.answer)
                    else:
                        text = st.write_stream(pipe.stream(turn, params))
                        pipe.finalize(turn, text if isinstance(text, str) else "".join(text))
                    msg.update(content=turn.answer, hits=turn.hits, cited=turn.cited, refused=turn.refused,
                               timings=turn.timings, usage=turn.usage.__dict__,
                               standalone=turn.standalone_question if turn.standalone_question != prompt else None)
                except Exception as exc:  # noqa: BLE001
                    err = friendly_error(exc) if "genai" in type(exc).__module__ else \
                        f"No se pudo completar la consulta: {type(exc).__name__}: {str(exc)[:200]}"
                    st.error(err)
                    msg.update(content=f"⚠️ {err}", hits=[], cited=[])
                render_sources(msg, key="new")
        st.session_state.messages.append(msg)


# --------------------------------------------------------------------------------------
# 2) GESTIÓN DOCUMENTAL
# --------------------------------------------------------------------------------------
with tab_docs:
    st.markdown("### Gestión de la base documental y vectorial")
    try:
        stats, sources = index_stats()
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudo leer el índice: {exc}")
        stats, sources = None, []

    if stats:
        c = st.columns(5)
        c[0].metric("Vectores", stats["vectores"])
        c[1].metric("Fuentes", stats["fuentes"])
        c[2].metric("Dimensión", stats["dim"])
        c[3].metric("Tamaño en Supabase", stats["tamano"])
        c[4].metric("pgvector", stats["pgvector"])
        with st.expander("Índices de la tabla"):
            for ix in stats["indices"]:
                st.code(ix["indexdef"], language="sql")

        src_df = pd.DataFrame(sources)
        if not src_df.empty:
            src_df["cargado"] = pd.to_datetime(src_df["cargado"]).dt.strftime("%Y-%m-%d %H:%M")
            src_df = src_df.drop(columns=["documento"])
            left, right = st.columns([3, 2])
            left.dataframe(src_df, hide_index=True, use_container_width=True,
                           column_config={"fragmentos": st.column_config.ProgressColumn(
                               "fragmentos", format="%d", min_value=0, max_value=int(src_df["fragmentos"].max()))})
            right.bar_chart(src_df.groupby("doc_type")["fragmentos"].sum(), horizontal=True, height=220)

            st.markdown("#### Explorar fragmentos")
            sel = st.selectbox("Fuente", src_df["source"].tolist())
            chunks = store.chunks(sel)
            st.caption(f"{len(chunks)} fragmentos · tamaño medio "
                       f"{sum(ch['caracteres'] for ch in chunks) / max(len(chunks), 1):.0f} caracteres")
            for ch in chunks:
                with st.expander(f"#{ch['chunk_index']} · {(ch['title'] or '').split(' - ')[-1]} "
                                 f"({ch['caracteres']} car.)"):
                    st.markdown(ch["content"])
                    st.json(ch["metadata"], expanded=False)

    st.divider()
    up_col, del_col = st.columns(2)
    with up_col:
        st.markdown("#### ➕ Agregar documentos")
        st.caption("Se fragmentan igual que en el ACA 1 (secciones + 800/120), se vectorizan localmente con "
                   "Ollama y se suben a Supabase con *upsert* idempotente.")
        files = st.file_uploader("Archivos .md, .txt o .pdf", type=[e[1:] for e in ALLOWED_EXT],
                                 accept_multiple_files=True)
        save_copy = st.checkbox("Guardar copia en data/corpus/ (recomendado: así el notebook del ACA 1 la conserva)",
                                value=True)
        if st.button("Indexar", type="primary", disabled=not files):
            for f in files:
                with st.status(f"Procesando {f.name}…", expanded=False) as status:
                    try:
                        data = f.getvalue()
                        recs = chunk_docs(load_file(f.name, data), S.chunk_size, S.chunk_overlap)
                        if not recs:
                            raise ValueError("No se extrajo texto (¿PDF escaneado?)")
                        st.write(f"{len(recs)} fragmentos")
                        embs = embedder.embed_documents(recs)
                        store.upsert(recs, embs)
                        removed = store.delete_source(f.name, keep_ids=[make_chunk_id(r) for r in recs])
                        if save_copy:
                            CORPUS_DIR.mkdir(parents=True, exist_ok=True)
                            (CORPUS_DIR / f.name).write_bytes(data)
                        status.update(label=f"✅ {f.name}: {len(recs)} fragmentos indexados"
                                            + (f", {removed} obsoletos eliminados" if removed else ""),
                                      state="complete")
                    except Exception as exc:  # noqa: BLE001
                        status.update(label=f"❌ {f.name}: {exc}", state="error")
            index_stats.clear()
            health.clear()

    with del_col:
        st.markdown("#### 🗑️ Eliminar un documento")
        doc_sources = [s["source"] for s in sources if s["doc_type"] == "documento"]
        target = st.selectbox("Documento", doc_sources, index=None, placeholder="Selecciona…")
        also_file = st.checkbox("Eliminar también el archivo de data/corpus/")
        confirm = st.checkbox("Confirmo que quiero borrar sus vectores de Supabase")
        if st.button("Eliminar", disabled=not (target and confirm)):
            n = store.delete_source(target)
            if also_file and (CORPUS_DIR / target).exists():
                (CORPUS_DIR / target).unlink()
            st.success(f"{n} vectores de {target} eliminados")
            index_stats.clear()
            health.clear()


# --------------------------------------------------------------------------------------
# 3) CONSULTA VECTORIAL (sin LLM)
# --------------------------------------------------------------------------------------
with tab_search:
    st.markdown("### Panel de consulta semántica")
    st.caption("Recuperación pura (Top-k) para inspeccionar qué contexto recibiría el LLM.")
    q = st.text_input("Consulta", "¿Qué significa un defecto reversible en la gammagrafía con talio?")
    k2 = st.slider("Top-k", 1, 15, 5, key="k_search")
    if st.button("Buscar", type="primary") and q:
        try:
            t = {}
            hits = pipe.retrieve(q, k=k2, doc_type=doc_filter, timings=t)
            m = st.columns(3)
            m[0].metric("Embedding local", f"{t['embedding_ms']:.0f} ms")
            m[1].metric("Búsqueda Supabase", f"{t['busqueda_ms']:.0f} ms")
            m[2].metric("Mejor similitud", f"{hits[0]['similarity']:.3f}" if hits else "—",
                        delta="sobre el umbral" if hits and hits[0]["similarity"] >= threshold else "bajo el umbral",
                        delta_color="normal" if hits and hits[0]["similarity"] >= threshold else "inverse")
            df = pd.DataFrame([{"#": i, "similitud": round(h["similarity"], 4), "fuente": h["source"],
                                "sección": short_title(h), "tipo": h["doc_type"],
                                "fragmento": " ".join(h["content"].split())[:220]}
                               for i, h in enumerate(hits, start=1)])
            st.dataframe(df, hide_index=True, use_container_width=True,
                         column_config={"similitud": st.column_config.ProgressColumn(
                             "similitud", format="%.3f", min_value=0.0, max_value=1.0)})
            with st.expander("Ver el prompt que se enviaría a Gemini"):
                st.markdown("**System prompt**")
                st.code(SYSTEM_PROMPT, language="markdown", wrap_lines=True)
                st.markdown("**Mensaje de usuario con el contexto inyectado**")
                st.code(build_user_message(q, hits[:top_k]), language="markdown", wrap_lines=True)
        except Exception as exc:  # noqa: BLE001
            st.error(f"{type(exc).__name__}: {exc}")


# --------------------------------------------------------------------------------------
# 4) EVALUACIÓN
# --------------------------------------------------------------------------------------
with tab_eval:
    st.markdown("### Validación integral (PASO 5)")
    st.caption(f"{len(TEST_CASES)} casos: preguntas de dominio, sobre los datos, una consulta compleja, preguntas "
               "fuera de dominio y un intento de *prompt injection*. Se mide recuperación, citas, abstención y latencia.")
    pause = st.slider("Pausa entre llamadas (s)", 0.0, 10.0, 4.0, 0.5,
                      help="Evita superar el límite de peticiones por minuto de la capa gratuita de Gemini.")
    if st.button("▶️ Ejecutar evaluación", type="primary", disabled=llm is None):
        bar = st.progress(0.0, text="Iniciando…")
        try:
            st.session_state.eval_df = run_evaluation(
                pipe, params, k=top_k, threshold=threshold, pause_s=pause,
                progress=lambda p, q: bar.progress(p, text=q[:90]))
        except Exception as exc:  # noqa: BLE001
            st.error(friendly_error(exc))
        bar.empty()

    df = st.session_state.eval_df
    if df is not None:
        s = summarize(df, top_k)
        c = st.columns(5)
        c[0].metric("Exactitud global", f"{s['exactitud_global']:.0%}")
        c[1].metric(f"Hit@{top_k}", f"{s[f'hit@{top_k}']:.0%}")
        c[2].metric("Respuestas con cita", f"{s['respuestas_con_cita']:.0%}")
        c[3].metric("Abstención fuera de dominio", f"{s['abstencion_fuera_dominio']:.0%}")
        c[4].metric("Latencia media", f"{s['latencia_media_ms'] / 1000:.2f} s")
        st.dataframe(df.drop(columns=["respuesta"]), hide_index=True, use_container_width=True,
                     column_config={"correcto": st.column_config.CheckboxColumn("correcto")})
        lat = df.set_index(df.index.map(lambda i: f"Q{i + 1:02d}"))[["embedding_ms", "busqueda_ms", "llm_ms"]]
        st.markdown("**Latencia por etapa (ms)**")
        st.bar_chart(lat, horizontal=True, stack=True)
        with st.expander("Ver respuestas completas"):
            for i, r in df.iterrows():
                st.markdown(f"**Q{i + 1}. {r['pregunta']}**  \n{r['respuesta']}")
        st.download_button("⬇️ Descargar resultados (CSV)", df.to_csv(index=False).encode("utf-8"),
                           file_name="evaluacion_rag.csv")


# --------------------------------------------------------------------------------------
# 5) ARQUITECTURA
# --------------------------------------------------------------------------------------
with tab_arch:
    st.markdown("### Arquitectura RAG end-to-end")
    c1, c2 = st.columns([2, 3])
    with c1:
        st.graphviz_chart("""
digraph G {
  rankdir=TB; bgcolor="transparent"; nodesep=0.3; ranksep=0.35;
  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12, width=2.6];
  edge [fontname="Helvetica", fontsize=10, color="#607D8B"];
  u   [label="Usuario · interfaz Streamlit", fillcolor="#E3F2FD"];
  rw  [label="Reescritura con historial\n(Gemini, opcional)", fillcolor="#FFF3E0"];
  emb [label="Embedding local de la pregunta\nOllama · EmbeddingGemma 768 d", fillcolor="#E8F5E9"];
  db  [label="Supabase (nube) · PostgreSQL + pgvector\nHNSW · coseno · RLS · rag_salud", fillcolor="#E0F2F1"];
  th  [label="¿similitud Top-1\n≥ umbral?", shape=diamond, fillcolor="#FCE4EC", width=1.8];
  no  [label="«No encontré información»\n(sin llamar al LLM)", fillcolor="#FFEBEE"];
  pr  [label="Prompt: reglas del sistema +\nfragmentos numerados [1]..[k]", fillcolor="#F3E5F5"];
  llm [label="Google Gemini API (nube)", fillcolor="#FFF3E0"];
  out [label="Respuesta con citas [n]\n+ panel de fuentes", fillcolor="#E3F2FD"];
  u -> rw -> emb; emb -> db [label=" vector"]; db -> th [label=" Top-k"];
  th -> pr [label=" sí"]; th -> no [label=" no"]; pr -> llm -> out;
}""", use_container_width=True)
    with c2:
        st.markdown(f"""
**Configuración actual**

| Parámetro | Valor | Justificación |
|---|---|---|
| Modelo | `{model}` | Capa gratuita de Gemini, baja latencia, contexto amplio |
| Temperatura | {temperature} | Baja para respuestas factuales y reproducibles |
| Top-p | {top_p} | Recorta la cola de tokens improbables |
| Máx. tokens | {max_tokens} | Respuestas de ~250 palabras con citas |
| Top-k | {top_k} | Suficiente cobertura sin diluir el contexto |
| Umbral | {threshold} | Punto medio entre consultas de dominio (≈0.81) y fuera de dominio (≈0.60) del ACA 1 |
""")
        st.markdown("**System prompt**")
        st.code(SYSTEM_PROMPT, language="markdown", wrap_lines=True)
