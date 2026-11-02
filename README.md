<<<<<<< HEAD
# ACA 1 · Computación en la Nube — RAG clínico con Ollama + Supabase pgvector

Pipeline de ingesta, chunking, **embeddings locales (EmbeddingGemma vía Ollama)** y búsqueda semántica sobre **Supabase + pgvector**.

- **Pilar:** Salud (asistente cloud de consulta clínica, diagnóstico asistido y protocolos)
- **Datasets base:** UCI Heart Disease (920 pacientes) y UCI Breast Cancer Wisconsin – Diagnostic (569 biopsias)
- **Corpus complementario:** guía de riesgo cardiovascular, guía de cáncer de mama, protocolo de bioseguridad y consentimiento informado

## Arquitectura

```
 data/corpus (.md/.pdf) ─┐
 data/*.csv (UCI) ───────┼─► chunking (800/120) ─► Ollama · EmbeddingGemma (local, 768 d, $0)
                         │                                   │  solo viajan los vectores
                         │                                   ▼
                         │                     Supabase (nube) · PostgreSQL + pgvector
                         │                     tabla rag_salud · índice HNSW · coseno · RLS
                         │                                   ▲
 pregunta del usuario ───┴─► Ollama (prefijo de consulta) ───┘ ─► Top-k + similitud coseno
```

## Estructura

```
ESP-rag/
├── notebooks/ACA1_RAG_Salud_Ollama_pgvector.ipynb   # entregable principal
├── sql/01_schema_salud.sql                         # tabla, índice HNSW (coseno), RLS, match_salud()
├── data/
│   ├── heart_disease_uci.csv
│   ├── BreastCancer.csv
│   └── corpus/                                     # documentos .md/.txt/.pdf
├── poster/poster_template.html                     # póster A3; el notebook genera poster/poster_ACA1.html
├── GUION_VIDEO.md                                  # guion de la sustentación (3–5 min)
├── .env.example                                    # plantilla de credenciales
├── requirements.txt
├── .gitignore                                      # excluye .env
└── _educacion_anterior/                            # versión previa (pilar Educación + Gemini), no se usa
```

## Cómo ejecutarlo (Mac)

1. **Ollama:** instala la app desde https://ollama.com/download y descarga el modelo:
   ```bash
   ollama pull embeddinggemma
   ollama list            # debe aparecer embeddinggemma:latest
   ```
2. **Credenciales:** `cp .env.example .env` y pega en `DATABASE_URL` la cadena del *Session pooler* de Supabase (botón **Connect** del proyecto).
3. **Entorno Python:**
   ```bash
   cd ~/ESP-rag
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   jupyter lab
   ```
4. Abre `notebooks/ACA1_RAG_Salud_Ollama_pgvector.ipynb` y ejecuta **Run → Run All Cells**. El notebook crea la tabla `rag_salud` por sí solo.

## Antes de entregar

- [ ] (Recomendado) Agregar 1–2 PDF oficiales en `data/corpus/` (p. ej. GPC de cáncer de mama del MinSalud, paquete técnico HEARTS de la OMS). Los 3 `.md` incluidos son documentos de apoyo académico.
- [ ] Ejecutar el notebook completo y guardarlo **con las salidas** (las métricas y la gráfica cambian con el modelo real).
- [ ] Revisar que las consultas de validación y el `UMBRAL` de la demo tengan sentido con tus resultados.
- [ ] Verificar que `.env` no esté en el repositorio (`git status`).
- [ ] **Póster:** en la celda «Generar el póster» del notebook pon tus autores, `REPO_URL` y `VIDEO_URL`, ejecútala y abre `poster/poster_ACA1.html` en Chrome → Imprimir → Guardar como PDF (tamaño A3, márgenes «Ninguno», «Gráficos de fondo» activado).
- [ ] Video de 3 a 5 minutos (ver `GUION_VIDEO.md`).

## Mapa contra la rúbrica

| Criterio | Dónde está |
|---|---|
| Aprovisionamiento cloud y conectividad (20 %) | Sección 2: Supabase, HNSW + coseno, RLS, `.env` |
| Calidad de datos y chunking (20 %) | Secciones 3 y 4: corpus por secciones, tabla comparativa de tamaños, justificación 800/120 |
| Embeddings e indexación (20 %) | Secciones 1 y 5: EmbeddingGemma vía Ollama con prefijos de tarea, lotes de 32, batch upsert idempotente |
| Validación de búsqueda semántica (15 %) | Secciones 6 y 7: Top-k, similitud coseno, Hit@1/Hit@5, MRR, control negativo, latencia |
| Póster (15 %) y video (10 %) | `GUION_VIDEO.md` |
=======
# aca1_cp
>>>>>>> 2fee74405ea672c963eadaf3474b5224638c18b7
