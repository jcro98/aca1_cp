# Guion · Video de sustentación ACA 1 (≈ 4 min 30 s)

**Proyecto:** RAG clínico con embeddings locales (Ollama + EmbeddingGemma 2) y base vectorial en la nube (Supabase + pgvector)
**Pilar:** Salud · **Duración:** ~600 palabras de narración (≈ 4:15) + ~15 s de ejecución en vivo. Límite: 3 a 5 min.

### Antes de grabar

- [ ] Notebook ejecutado completo con *Restart Kernel and Run All* (números de celda en orden).
- [ ] Ollama abierto; una terminal lista con `ollama list` (debe aparecer `embeddinggemma-2`).
- [ ] Supabase abierto en dos pestañas: **Table Editor → rag_salud** y **Database → Indexes**.
- [ ] Póster PDF abierto (para mostrar la arquitectura y cerrar).
- [ ] Zoom del navegador / Jupyter al 125–150 % (Cmd +). Cerrar cualquier ventana donde se vea el `.env`.

---

## 1 · Problema y pregunta orientadora · 0:00 – 0:30

**Pantalla:** póster completo o portada del notebook.

> Hola, soy Juan Reyes y presento el ACA 1 de Computación en la Nube, en el pilar de **Salud**. En un servicio clínico la información está dispersa: guías extensas, protocolos y tablas de datos. Buscar por palabras clave no entiende la pregunta. Por eso nos preguntamos: ¿cómo construir un pipeline en la nube que indexe documentos clínicos y los recupere por significado, con alta precisión, **costo cero** y baja latencia?

## 2 · Corpus y datasets · 0:30 – 1:10

**Pantalla:** carpeta `data/corpus/` → celda de la sección 3 (tabla de documentos y conteos de los datasets).

> El corpus tiene tres documentos: una **guía de riesgo cardiovascular**, una **guía de detección de cáncer de mama** y un **protocolo de bioseguridad y consentimiento informado**. Los complementamos con dos datasets de UCI: **Heart Disease**, con 920 pacientes, y **Breast Cancer Wisconsin**, con 569 biopsias. No indexamos filas de pacientes: convertimos en texto el **diccionario de variables** y **resúmenes estadísticos**, como la prevalencia de enfermedad por tipo de dolor torácico. Así el asistente responde con la guía y también con evidencia de los datos.

## 3 · Chunking · 1:10 – 1:40

**Pantalla:** tabla comparativa 300 / 500 / 800 / 1200 (resaltar la fila de 800).

> Cada documento se divide primero por secciones y luego con `RecursiveCharacterTextSplitter`, en fragmentos de **800 caracteres con 120 de solapamiento**. Con 300, casi un tercio de los fragmentos queda sin contexto; con 1.200 se mezclan temas. Con 800, cada fragmento conserva un criterio completo: el umbral y su interpretación. En total indexamos **72 vectores**.

## 4 · Arquitectura y herramientas cloud · 1:40 – 2:35

**Pantalla:** diagrama de arquitectura del póster → terminal con `ollama list` → Supabase: tabla `rag_salud` → pestaña de índices (HNSW).

> La arquitectura es híbrida. Los embeddings se generan **en mi equipo** con **Ollama** y el modelo **EmbeddingGemma 2** de Google, de 768 dimensiones y multilingüe. No pagamos ninguna API, y en salud hay una ventaja extra: el texto clínico **no sale del equipo**; a la nube solo viajan los vectores.
>
> Los vectores se guardan en **Supabase**, PostgreSQL gestionado con **pgvector**, en el plan gratuito. Lo elegimos porque guarda vectores, metadatos y SQL en un solo servicio. Aquí está la tabla `rag_salud`, con un índice **HNSW por distancia coseno** y seguridad a nivel de fila. Las credenciales se leen de un `.env` que no se sube al repositorio, y la carga es por lotes con *upsert*, así que re-ejecutar no duplica datos.

## 5 · Demo en vivo y validación · 2:35 – 4:05

**Pantalla:** celda «Demo en vivo» → ejecutar → bajar a la tabla de métricas y la gráfica → control negativo.

> Ahora, una consulta en tiempo real contra el clúster: *«¿Qué se le debe explicar a un paciente antes de una biopsia de mama?»*.
>
> *(Ejecutar la celda y esperar el resultado.)*
>
> La pregunta se vectorizó localmente, la búsqueda corrió en Supabase y en menos de un cuarto de segundo tenemos los fragmentos más cercanos: la sección de comunicación con la paciente, con similitud 0,84, y la de consentimiento informado, con 0,79.
>
> Para validar definimos diez consultas con su fuente esperada. Obtuvimos **Hit@1 del 90 %, Hit@5 del 100 % y un MRR de 0,95**, con similitud promedio de 0,81. El único fallo en primera posición fue la pregunta sobre consentimiento antes de una prueba de esfuerzo: primero trajo la guía cardiovascular, que también lo menciona, y el protocolo quedó segundo.
>
> Con el **control negativo**, una pregunta sobre la bandeja paisa, la similitud cae a 0,60. Esa brecha nos permite fijar un umbral de 0,70 para que el asistente diga «no tengo información» en lugar de inventar. La latencia es de unos 240 milisegundos por consulta.

## 6 · Cierre · 4:05 – 4:30

**Pantalla:** póster completo con los enlaces.

> En resumen: una base vectorial en la nube con Supabase y pgvector, un corpus clínico que integra guías y datasets, embeddings locales a costo cero y una validación cuantitativa de la búsqueda. El siguiente paso es conectar estos fragmentos a un modelo de lenguaje para responder citando la fuente. El código y el póster están en el repositorio. Gracias.

---

### Consejos

- Graben con la grabación de pantalla de macOS (Cmd + Shift + 5) o con Loom; micrófono cerca y sin ruido de fondo.
- Lean el guion un par de veces en voz alta antes; no tiene que ser palabra por palabra.
- Si la búsqueda en vivo tarda o falla, sigan con los resultados ya ejecutados de la sección 7.
- Si se pasan de 5 minutos, recorten el bloque 3 a una frase.
