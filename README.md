# Asistente Clínico RAG · Computación en la Nube (CUN)

Sistema RAG end-to-end para el **pilar Salud**:

- **ACA 1:** ingesta, chunking, embeddings locales (**EmbeddingGemma vía Ollama**) e índice vectorial en **Supabase + pgvector** (`notebooks/ACA1_RAG_Salud_Ollama_pgvector.ipynb`).
- **ACA 2:** integración del LLM **Google Gemini (API en la nube)** y una **interfaz Streamlit** con chat RAG, citas de fuentes, gestión documental, panel de consulta y evaluación (`app.py`).

**Autor:** Juan Carlos Reyes Ospina · Especialización en Inteligencia Artificial · Docente: Dr. Hamilton Rivera Flor

## Arquitectura (ACA 2)

```
             ┌────────────────────────── Streamlit (app.py) ──────────────────────────┐
 usuario ──► │ Chat con historial · Gestión documental · Consulta vectorial · Evaluación │
             └──────┬──────────────────────────────────────────────────────▲───────────┘
                    │ pregunta (+ reescritura con historial, Gemini)        │ respuesta + citas [n]
                    ▼                                                       │
     Ollama · EmbeddingGemma (local, 768 d)                                 │
                    │ solo viaja el vector                                  │
                    ▼                                                       │
     Supabase (nube) · PostgreSQL + pgvector ── Top-k (HNSW, coseno) ──► ¿sim ≥ umbral?
     tabla rag_salud (ACA 1) · RLS                                 no │          │ sí
                                                       «No encontré información»  ▼
                                                                    Prompt: reglas + fragmentos [1]..[k]
                                                                                 │
                                                                    Google Gemini API (nube) ─────┘
```

## Estructura

```
ESP-rag/
├── app.py                         # ACA 2 · interfaz Streamlit
├── rag/                           # ACA 2 · paquete del pipeline
│   ├── config.py                  #   lectura de .env / st.secrets (sin claves en código)
│   ├── embeddings.py              #   Ollama + EmbeddingGemma (mismos prefijos que el ACA 1)
│   ├── vectorstore.py             #   Supabase pgvector: búsqueda Top-k, inventario, upsert, borrado
│   ├── ingest.py                  #   carga .md/.txt/.pdf con el mismo chunking del ACA 1 (800/120)
│   ├── llm.py                     #   cliente Gemini (google-genai), streaming, reintentos
│   ├── pipeline.py                #   prompt, inyección de contexto, umbral, citas, reescritura
│   └── evaluation.py              #   casos de prueba y métricas (PASO 5)
├── scripts/evaluar_rag.py         # evaluación por consola -> results/evaluacion_rag.csv
├── notebooks/ACA1_RAG_Salud_Ollama_pgvector.ipynb
├── sql/01_schema_salud.sql        # tabla, índice HNSW (coseno), RLS, match_salud()
├── data/ (CSV UCI + corpus/)      # documentos .md/.txt/.pdf
├── .streamlit/config.toml         # tema de la app
├── .env.example                   # plantilla de credenciales
└── requirements.txt
```

## Cómo ejecutarlo (Mac)

1. **Ollama** abierto con el modelo de embeddings del ACA 1:
   ```bash
   ollama list                 # debe aparecer embeddinggemma-2 (o el nombre que pusiste en EMBED_MODEL)
   ```
2. **API key de Gemini (gratis):** créala en <https://aistudio.google.com/apikey>.
3. **Credenciales:** en la raíz del proyecto
   ```bash
   cp .env.example .env        # si ya tenías .env del ACA 1, solo agrega GEMINI_API_KEY y GEMINI_MODEL
   ```
   Completa `DATABASE_URL` (Session pooler de Supabase) y `GEMINI_API_KEY`.
4. **Entorno e instalación:**
   ```bash
   cd ~/ESP-rag
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
5. **Índice vectorial:** si la tabla `rag_salud` ya tiene datos del ACA 1 no hay que hacer nada; si no, ejecuta el notebook del ACA 1 completo.
6. **App:**
   ```bash
   streamlit run app.py
   ```
   Se abre en <http://localhost:8501>.

Evaluación por consola (opcional): `python scripts/evaluar_rag.py --pausa 4`

## Módulos de la interfaz

| Pestaña | Qué hace |
|---|---|
| 💬 **Chat** | Conversación con historial, respuesta en *streaming*, citas `[n]` y panel de fuentes (citadas / recuperadas, similitud coseno). Reescribe preguntas de seguimiento («¿y en mujeres?») antes de buscar. Exporta la conversación a Markdown. |
| 📚 **Gestión documental** | Métricas del índice (vectores, fuentes, dimensión, tamaño, versión de pgvector, índices), tabla de fuentes, explorador de fragmentos con metadatos, **carga** de nuevos `.md/.txt/.pdf` (chunking + embeddings + upsert) y **eliminación** de documentos. |
| 🔎 **Consulta vectorial** | Búsqueda Top-k sin LLM, latencias de embedding y de Supabase, y vista del prompt exacto que recibiría Gemini. |
| 🧪 **Evaluación** | 11 casos (dominio, datos, consulta compleja, fuera de dominio y *prompt injection*): Hit@k, MRR, % de respuestas con cita, % de abstención, latencia por etapa y descarga en CSV. |
| 🧭 **Arquitectura** | Diagrama del flujo, hiperparámetros activos y *system prompt*. |

La barra lateral muestra el estado de Supabase, Ollama y Gemini, y permite cambiar modelo, temperatura, top-p, máx. tokens, Top-k, umbral y filtro por tipo de fuente.

## Decisiones técnicas

**¿Por qué Gemini por API?** Capa gratuita sin tarjeta, baja latencia, ventana de contexto amplia, buen desempeño en español y SDK oficial (`google-genai`). No requiere GPU local, a diferencia de correr Gemma/Llama con Ollama. Los embeddings siguen siendo locales para reutilizar el índice del ACA 1 sin re-vectorizar y para que el texto clínico de los documentos no salga del equipo al indexar.

| Hiperparámetro | Valor | Justificación |
|---|---|---|
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modelo «flash» de la capa gratuita; el selector lista los modelos disponibles para tu clave |
| `temperature` | 0.2 | Respuestas factuales y reproducibles; menos riesgo de inventar |
| `top_p` | 0.9 | Recorta la cola de tokens improbables |
| `max_output_tokens` | 1024 | Respuestas de ~250 palabras con viñetas y citas |
| `top_k` | 5 | En el ACA 1, Hit@5 = 100 %: cubre la fuente correcta sin diluir el contexto |
| `SIM_THRESHOLD` | 0.70 | Punto medio entre la similitud Top-1 en dominio (≈0.81) y fuera de dominio (≈0.60) medida en el ACA 1 |
| historial | 6 mensajes | Coherencia conversacional sin inflar el prompt |

**Mitigación de alucinaciones**

1. *System prompt* con reglas estrictas: responder solo con el CONTEXTO, citar `[n]`, no inventar cifras y decirlo cuando falta información.
2. **Guardarraíl por umbral:** si el mejor fragmento no supera el umbral, la app responde «No encontré información…» **sin llamar al LLM**.
3. Fragmentos numerados con fuente, sección y similitud; la UI marca cuáles se citaron realmente.
4. Los fragmentos se tratan como datos (regla contra *prompt injection*), y se aclara que las estadísticas de los datasets no son probabilidades individuales.

**Seguridad de credenciales:** `DATABASE_URL` y `GEMINI_API_KEY` se leen solo de `.env` (o `st.secrets` / Colab Secrets). `.env` y `.streamlit/secrets.toml` están en `.gitignore`; la tabla tiene RLS activo.

## Antes de entregar

- [ ] `git status` no muestra `.env`.
- [ ] Ejecutar la pestaña **Evaluación** (o `scripts/evaluar_rag.py`) y guardar capturas/CSV para el póster y el video.
- [ ] Capturas de las pestañas Chat (con fuentes abiertas) y Gestión documental para el póster.

## Referencias

- Google. (2025). *Gemini API documentation*. https://ai.google.dev/gemini-api/docs
- Google DeepMind. (2024). *Gemma: Open models based on Gemini research and technology*. https://arxiv.org/abs/2403.08295
- Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems, 33*, 9459–9474. https://arxiv.org/abs/2005.11401
- Streamlit Inc. (2024). *Streamlit documentation*. https://docs.streamlit.io/
- Supabase. (2024). *pgvector: Embeddings and vector similarity*. https://supabase.com/docs/guides/database/extensions/pgvector
- Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1988). *Heart Disease* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C52P4X
- Wolberg, W., Mangasarian, O., Street, N., & Street, W. (1995). *Breast Cancer Wisconsin (Diagnostic)* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5DW2B
