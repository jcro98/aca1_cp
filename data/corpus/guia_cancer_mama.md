# Guía de apoyo clínico: detección temprana y diagnóstico del cáncer de mama

> Documento de apoyo académico elaborado a partir de lineamientos públicos (Ministerio de Salud y Protección Social de Colombia, Guía de Práctica Clínica de cáncer de mama 2013; OMS, Iniciativa Mundial contra el Cáncer de Mama). Resume criterios generales para un asistente de consulta. No reemplaza la guía oficial ni el criterio médico.

## 1. Propósito y alcance

Esta guía resume la detección temprana, la clasificación de hallazgos en imágenes y el estudio citológico e histológico de lesiones mamarias. Los conceptos de citología por aspiración se relacionan con el dataset Breast Cancer Wisconsin (Diagnostic), cuyas variables describen los núcleos celulares obtenidos por aspiración con aguja fina.

## 2. Factores de riesgo

El principal factor de riesgo es la edad: la mayoría de los casos se diagnostica después de los 50 años. Otros factores son los antecedentes familiares de cáncer de mama u ovario, las mutaciones de los genes BRCA1 y BRCA2, la menarquia temprana, la menopausia tardía, no haber tenido hijos o tener el primer hijo después de los 30 años, la terapia hormonal de reemplazo prolongada, la obesidad después de la menopausia, el consumo de alcohol y la radiación previa en el tórax. Tener factores de riesgo no significa que se desarrollará la enfermedad, y muchas mujeres diagnosticadas no tienen ningún factor conocido.

## 3. Detección temprana (tamización)

Según la Guía de Práctica Clínica del Ministerio de Salud de Colombia:

- **Mamografía de tamización:** cada dos años en mujeres de 50 a 69 años, acompañada de la lectura con el sistema BI-RADS.
- **Examen clínico de la mama:** realizado por personal de salud entrenado, anualmente a partir de los 40 años.
- **Autoconocimiento de la mama:** se promueve que la mujer conozca la apariencia normal de sus mamas y consulte ante cualquier cambio; no sustituye la mamografía.

Las mujeres con riesgo alto (mutación BRCA o antecedente familiar fuerte) requieren un esquema de seguimiento individualizado que puede iniciar antes de los 40 años e incluir resonancia magnética.

## 4. Signos de alarma

Se debe consultar sin esperar la siguiente tamización ante cualquiera de estos signos: masa o nódulo palpable en la mama o la axila, retracción reciente del pezón, secreción sanguinolenta por el pezón, cambios en la piel como enrojecimiento o aspecto de piel de naranja, ulceración o cambio en el tamaño o la forma de la mama. Ante una masa palpable en una mujer de cualquier edad se indica estudio con imágenes diagnósticas (mamografía y/o ecografía) aunque la mamografía previa haya sido normal.

## 5. Clasificación BI-RADS

El sistema BI-RADS (Breast Imaging Reporting and Data System) estandariza el informe de la mamografía y la ecografía:

- **BI-RADS 0:** estudio incompleto; requiere imágenes adicionales.
- **BI-RADS 1:** negativo.
- **BI-RADS 2:** hallazgo benigno; continuar tamización de rutina.
- **BI-RADS 3:** probablemente benigno (probabilidad de malignidad menor del 2 %); control con imágenes a los 6 meses.
- **BI-RADS 4:** anormalidad sospechosa; se recomienda biopsia.
- **BI-RADS 5:** altamente sugestivo de malignidad (95 % o más); biopsia obligatoria.
- **BI-RADS 6:** malignidad ya confirmada por biopsia.

## 6. Estudio de la lesión: citología y biopsia

La **biopsia por aspiración con aguja fina (BACAF)** obtiene células de la lesión con una aguja delgada. Es rápida y poco invasiva, y su resultado se basa en la morfología de los núcleos celulares. La **biopsia con aguja gruesa (trucut)**, guiada por ecografía o estereotaxia, obtiene un cilindro de tejido y es el método preferido para confirmar el diagnóstico, porque permite distinguir el carcinoma in situ del invasivo y realizar estudios de receptores hormonales y HER2.

En la citología, los núcleos malignos tienden a ser más grandes, con contornos irregulares, cromatina gruesa y mayor variación de tamaño entre células. El dataset Breast Cancer Wisconsin (Diagnostic) describe digitalmente estas características para cada imagen de BACAF: radio, textura, perímetro, área, suavidad, compacidad, concavidad, puntos cóncavos, simetría y dimensión fractal del núcleo. Para cada una se registran tres valores: la media, el error estándar y el peor valor (promedio de los tres valores más grandes). La variable diagnosis indica si la lesión es maligna (M) o benigna (B).

## 7. Ruta después del diagnóstico

Una vez confirmado el cáncer, la paciente debe ser valorada por un equipo multidisciplinario (cirugía de mama, oncología clínica, radioterapia, patología, psicología y trabajo social). El tratamiento depende del estadio (TNM), del subtipo molecular (receptores de estrógeno y progesterona, HER2, Ki-67) y de las preferencias de la paciente. La guía colombiana establece que el tiempo entre la sospecha y el inicio del tratamiento debe ser el menor posible, porque el diagnóstico temprano mejora de forma importante la supervivencia.

## 8. Comunicación con la paciente

El resultado de una biopsia se entrega en consulta presencial, con lenguaje claro, explicando el significado del hallazgo, los siguientes pasos y las opciones de tratamiento. La paciente tiene derecho a recibir una copia de su informe, a pedir una segunda opinión y a estar acompañada por una persona de confianza.
