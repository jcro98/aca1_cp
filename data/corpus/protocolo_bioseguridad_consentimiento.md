# Protocolo de bioseguridad, consentimiento informado y manejo de datos clínicos en servicios de diagnóstico

> Documento de apoyo académico elaborado a partir de lineamientos públicos (OMS, "Mis 5 momentos para la higiene de las manos"; normatividad colombiana: Ley 23 de 1981, Ley 1581 de 2012, Resolución 8430 de 1993). Resume criterios generales. No reemplaza los protocolos oficiales de la institución.

## 1. Alcance

Aplica al personal de los servicios de cardiología no invasiva (electrocardiografía, prueba de esfuerzo, gammagrafía) y de imágenes y patología mamaria (mamografía, ecografía, toma de biopsias), así como a quienes administran los datos clínicos derivados de estos servicios.

## 2. Precauciones estándar

Todo paciente se considera potencialmente infeccioso. Las precauciones estándar incluyen la higiene de manos, el uso de elementos de protección personal según el riesgo, el manejo seguro de elementos cortopunzantes, la limpieza y desinfección de equipos entre pacientes y la segregación correcta de residuos.

## 3. Higiene de manos: los 5 momentos de la OMS

1. Antes del contacto con el paciente.
2. Antes de realizar una tarea limpia o aséptica (por ejemplo, antes de una biopsia o de canalizar una vena).
3. Después del riesgo de exposición a fluidos corporales.
4. Después del contacto con el paciente.
5. Después del contacto con el entorno del paciente.

El lavado con agua y jabón dura de 40 a 60 segundos y es obligatorio cuando las manos están visiblemente sucias. La fricción con solución alcohólica dura de 20 a 30 segundos y es el método preferido en los demás casos.

## 4. Elementos de protección personal

- **Guantes:** para contacto con sangre, fluidos, mucosas o piel no intacta; se cambian entre pacientes y no reemplazan la higiene de manos.
- **Tapabocas y protección ocular:** en procedimientos con riesgo de salpicaduras, como la toma de biopsias.
- **Bata:** cuando exista riesgo de contaminar la ropa.

Durante la prueba de esfuerzo, los electrodos son de un solo uso y la banda, la bicicleta y los cables se desinfectan después de cada paciente.

## 5. Manejo de cortopunzantes y residuos

Las agujas no se reencapsulan, no se doblan ni se rompen. Se descartan inmediatamente en el contenedor rígido para cortopunzantes (guardián), que se cierra y se reemplaza cuando alcanza las tres cuartas partes de su capacidad. Los residuos con riesgo biológico (gasas con sangre, guantes contaminados, muestras) se depositan en bolsa roja. Las muestras de biopsia se rotulan con dos identificadores del paciente y se transportan en recipientes cerrados con fijador.

## 6. Accidente con riesgo biológico

Ante una punción o salpicadura con sangre: lavar la zona inmediatamente con abundante agua y jabón sin frotar con fuerza ni exprimir la herida; en mucosas, irrigar con agua o solución salina. Reportar de inmediato al jefe del servicio y a la administradora de riesgos laborales (ARL). El médico evaluará la necesidad de profilaxis posexposición; si está indicada para VIH, debe iniciarse idealmente en las primeras 2 horas y no después de 72 horas.

## 7. Consentimiento informado

Antes de procedimientos con riesgo, como la prueba de esfuerzo, la gammagrafía, la angiografía coronaria o la biopsia de mama, el paciente debe firmar el consentimiento informado. El documento debe explicar en lenguaje comprensible:

- en qué consiste el procedimiento y su objetivo;
- los riesgos previsibles y su frecuencia (por ejemplo, en la prueba de esfuerzo, arritmias o dolor torácico; en la biopsia, hematoma o infección);
- los beneficios esperados y las alternativas disponibles;
- el derecho a hacer preguntas y a revocar el consentimiento en cualquier momento, sin que ello afecte su atención.

La Ley 23 de 1981 (ética médica) establece que el médico debe advertir al paciente sobre los riesgos previstos. Si el paciente no puede decidir, firma su representante legal. El consentimiento se archiva en la historia clínica.

## 8. Protección de datos personales y uso secundario de datos

Los datos de salud son datos sensibles según la Ley 1581 de 2012. Su tratamiento requiere autorización expresa del titular, finalidad informada y medidas de seguridad. La historia clínica es reservada y solo puede ser consultada por el paciente, el equipo de salud tratante y las autoridades que la ley autorice.

Para investigación o para entrenar modelos de inteligencia artificial se deben usar datos anonimizados: se eliminan nombres, documentos de identidad, direcciones, fechas exactas y cualquier dato que permita reidentificar a la persona. La Resolución 8430 de 1993 clasifica la revisión de historias clínicas sin intervención como investigación sin riesgo, pero exige aprobación del comité de ética y garantía de confidencialidad. Los datasets públicos como UCI Heart Disease y Breast Cancer Wisconsin ya están anonimizados.

## 9. Seguridad de la información en la nube

Las credenciales de acceso a bases de datos en la nube (por ejemplo, la cadena de conexión de Supabase) se guardan en variables de entorno o gestores de secretos, nunca en el código ni en repositorios públicos. El acceso a las tablas se restringe con políticas de seguridad a nivel de fila (RLS) y con roles de mínimo privilegio. Los modelos de embeddings que se ejecutan localmente (por ejemplo, con Ollama) evitan enviar el texto clínico a servicios externos, lo que reduce el riesgo de exposición de información sensible.
