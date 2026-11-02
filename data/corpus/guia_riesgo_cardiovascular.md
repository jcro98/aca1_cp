# Guía de apoyo clínico: evaluación de enfermedad coronaria y riesgo cardiovascular

> Documento de apoyo académico elaborado a partir de lineamientos públicos (OMS, paquete técnico HEARTS; guías de práctica clínica de cardiología). Resume criterios generales para un asistente de consulta. No reemplaza la guía oficial ni el criterio médico. Para la entrega final puede complementarse con el PDF oficial correspondiente en `data/corpus/`.

## 1. Propósito y alcance

Esta guía orienta la valoración inicial de adultos con sospecha de enfermedad arterial coronaria en consulta externa. Describe los factores de riesgo, la clasificación del dolor torácico, la interpretación de la prueba de esfuerzo y de la gammagrafía de perfusión, y los signos de alarma que obligan a remitir a urgencias. Los términos usados coinciden con las variables del dataset UCI Heart Disease (edad, sexo, tipo de dolor torácico, presión arterial en reposo, colesterol, glucemia en ayunas, electrocardiograma en reposo, frecuencia cardíaca máxima, angina inducida por ejercicio, depresión del segmento ST, pendiente del ST, vasos coloreados por fluoroscopia y resultado de talio).

## 2. Factores de riesgo cardiovascular

Los factores de riesgo no modificables son la edad (hombres mayores de 45 años y mujeres mayores de 55 años), el sexo masculino y los antecedentes familiares de enfermedad coronaria temprana. Los factores modificables son la hipertensión arterial, el colesterol elevado, la diabetes, el tabaquismo, la obesidad, la inactividad física, la dieta alta en sodio y el consumo nocivo de alcohol.

El riesgo cardiovascular global se estima combinando varios factores y no uno solo. La OMS recomienda usar tablas de riesgo para decidir la intensidad del tratamiento: a mayor riesgo a 10 años, más intensivo debe ser el control de la presión arterial y del colesterol.

## 3. Presión arterial

La presión arterial se mide en reposo, con el paciente sentado al menos cinco minutos, y se expresa en mmHg. Se considera hipertensión una presión sistólica igual o mayor a 140 mmHg o una diastólica igual o mayor a 90 mmHg confirmada en mediciones repetidas. Algunas guías (American Heart Association, 2017) usan un umbral más bajo de 130/80 mmHg. Una presión igual o mayor a 180/110 mmHg con síntomas como dolor de cabeza intenso, dolor torácico o alteración neurológica es una urgencia hipertensiva y requiere atención inmediata.

## 4. Colesterol y glucemia

El colesterol total deseable es menor de 200 mg/dL; entre 200 y 239 mg/dL se considera limítrofe alto y desde 240 mg/dL, alto. El valor más importante para decidir tratamiento es el colesterol LDL, junto con el riesgo global del paciente.

La glucemia en ayunas normal es menor de 100 mg/dL. Entre 100 y 125 mg/dL corresponde a glucemia alterada en ayunas (prediabetes) y un valor igual o mayor a 126 mg/dL en dos mediciones confirma diabetes. El dataset UCI registra si la glucemia en ayunas supera 120 mg/dL (variable fbs), lo que indica alteración del metabolismo de la glucosa y aumenta el riesgo coronario.

## 5. Clasificación del dolor torácico

El dolor torácico se clasifica según tres criterios: (1) dolor o molestia opresiva retroesternal, (2) desencadenado por el esfuerzo físico o el estrés emocional y (3) que se alivia con el reposo o con nitroglicerina.

- **Angina típica:** cumple los tres criterios.
- **Angina atípica:** cumple dos de los tres criterios.
- **Dolor no anginoso:** cumple uno o ninguno de los criterios.
- **Asintomático:** el paciente no refiere dolor torácico. Paradójicamente, en el dataset UCI los pacientes asintomáticos son el grupo con mayor proporción de enfermedad, porque la isquemia silente es frecuente en personas mayores y en diabéticos.

## 6. Electrocardiograma en reposo

El electrocardiograma (ECG) en reposo puede ser normal aunque exista enfermedad coronaria. Las alteraciones de la onda ST-T (inversión de la onda T o elevación/depresión del ST mayor de 0,05 mV) sugieren isquemia. La hipertrofia ventricular izquierda (criterios de Estes) es frecuente en hipertensos de larga evolución y se asocia a mayor riesgo cardiovascular.

## 7. Prueba de esfuerzo

La prueba de esfuerzo evalúa la respuesta del corazón al ejercicio progresivo en banda o bicicleta. Antes de realizarla se debe firmar el consentimiento informado.

- **Frecuencia cardíaca máxima teórica:** se estima como 220 menos la edad. Si el paciente no alcanza el 85 % de ese valor, la prueba es submáxima y su capacidad para descartar isquemia es menor. Una frecuencia máxima alcanzada baja (variable thalch) se asocia con peor pronóstico.
- **Angina inducida por ejercicio** (variable exang): la aparición de dolor torácico durante la prueba es un hallazgo de alto valor para isquemia.
- **Depresión del segmento ST** (variable oldpeak): una depresión horizontal o descendente igual o mayor a 1 mm (0,1 mV) respecto al reposo se considera prueba positiva para isquemia. Cuanto mayor es la depresión, mayor es la probabilidad de enfermedad multivaso.
- **Pendiente del ST en el pico del ejercicio** (variable slope): la pendiente ascendente suele ser normal; la pendiente plana o descendente es más sugestiva de isquemia.

La prueba se detiene ante dolor torácico progresivo, caída de la presión arterial, arritmias graves, mareo o depresión del ST mayor de 2 mm.

## 8. Gammagrafía de perfusión con talio y angiografía

La gammagrafía de perfusión miocárdica con talio-201 (variable thal) compara la perfusión del músculo cardíaco en reposo y en esfuerzo:

- **Normal:** perfusión homogénea en ambas fases.
- **Defecto reversible:** zona con baja perfusión solo durante el esfuerzo; indica isquemia de miocardio viable que podría beneficiarse de revascularización.
- **Defecto fijo:** zona sin perfusión en reposo ni en esfuerzo; indica cicatriz por infarto previo.

La angiografía coronaria (cateterismo) es el estándar de referencia. El número de vasos principales con estenosis visibles por fluoroscopia (variable ca, de 0 a 3) se relaciona con la extensión de la enfermedad. En el dataset UCI el diagnóstico (variable num) toma valores de 0 (sin estrechamiento mayor del 50 % en ningún vaso) a 4; los valores de 1 a 4 indican enfermedad coronaria presente.

## 9. Signos de alarma y remisión a urgencias

Debe remitirse de inmediato a urgencias a todo paciente con dolor torácico en reposo de más de 20 minutos, dolor que se irradia al brazo, la mandíbula o la espalda acompañado de sudoración, náuseas o dificultad para respirar, síncope, o dolor torácico que empeora rápidamente. Estos síntomas pueden corresponder a un síndrome coronario agudo (infarto) y el tiempo hasta la reperfusión determina el pronóstico. No se debe programar una prueba de esfuerzo a un paciente con angina inestable.

## 10. Prevención y estilo de vida (estrategia HEARTS de la OMS)

La estrategia HEARTS de la OMS organiza la atención primaria cardiovascular en seis componentes: hábitos y estilos de vida saludables, protocolos clínicos basados en evidencia, acceso a medicamentos y tecnologías esenciales, manejo basado en el riesgo, trabajo en equipo y sistemas de monitoreo.

Las recomendaciones de estilo de vida incluyen dejar de fumar, realizar al menos 150 minutos semanales de actividad física moderada, consumir menos de 5 g de sal al día (menos de 2 g de sodio), aumentar el consumo de frutas y verduras, mantener un peso saludable y limitar el alcohol. En pacientes con riesgo alto se agregan medicamentos antihipertensivos y estatinas según el protocolo.
