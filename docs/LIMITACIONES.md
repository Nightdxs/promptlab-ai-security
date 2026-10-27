# Limitaciones y trabajo pendiente

Estado documentado: PromptLab 0.3.0, 27 de octubre de 2026. Los resultados corresponden a un laboratorio con datos y efectos ficticios.

## Lo que los resultados actuales cubren

Se dispone de pruebas de software, demos con acciones fijas y pilotos benignos con Qwen2.5:7b. La interfaz también ejecutó una consulta real con el modelo local. El entorno del modelo verificado es Fedora 44, Python 3.14.8 y Ollama 0.40.11, utilizando CPU. La suite de software también pasó en Ubuntu mediante GitHub Actions con Python 3.10 y 3.14, sin ejecutar un LLM. No se ha validado Kali.

En las evidencias incluidas no se ha ejecutado el corpus de ataques contra un LLM. Los bloqueos mostrados por las demos acreditan el comportamiento del control frente a llamadas programadas, no una tasa de protección de la IA.

## Evaluación incompleta de la tarea

El cumplimiento automático es mínimo. Busca hechos y evidencia de herramientas; no comprueba todas las contradicciones, afirmaciones falsas ni acciones adicionales. La línea de responsable está vinculada al fixture actual y no es un evaluador general de correos.

El piloto de 0.2.3 contiene un ejemplo: C0 envió un correo ficticio con datos inventados antes de otro correcto. El segundo acreditó el mínimo, aunque el conjunto de efectos incumplía la petición. El hallazgo se describe en [RESULTADOS.md](RESULTADOS.md).

Tampoco basta el orden de los eventos para acreditar que el modelo observó el documento antes de decidir un envío. Puede proponer lectura y envío dentro de una misma respuesta. La versión actual ejecuta ambas llamadas en orden sin obligar a un turno intermedio de observación.

## Cobertura y validez experimental

- El corpus es pequeño y conocido durante el desarrollo: cuatro plantillas de ataque y tres tareas benignas base con variantes.
- No hay una partición final independiente. Las nueve ejecuciones del piloto son tres tareas repetidas entre configuraciones.
- Se cambiaron instrucciones y criterios entre versiones. Sus tasas no aíslan el efecto de una defensa.
- El verificador de fugas utiliza coincidencia literal del canario. Puede perder divulgaciones transformadas, parciales o codificadas.
- El modelo y el servidor se identifican mediante metadatos de un servicio que se considera confiable. No hay atestación de su implementación.
- Una semilla fija no garantiza repetibilidad bit a bit entre equipos o versiones.
- La revisión adicional publicada fue realizada por el asistente después del lote; no es validación humana independiente.

Por estas razones no se afirma seguridad general, reducción demostrada de ASR ni cumplimiento de la hipótesis académica. La metodología y los denominadores están en [METODOLOGIA.md](METODOLOGIA.md).

## Operación de la interfaz

Los resultados terminados se conservan en archivos, pero los trabajos activos y el progreso en vivo se mantienen en memoria. Un reinicio pierde ese estado. La exclusión de una ejecución protege al proceso web, no a otra evaluación iniciada directamente por consola.

La interfaz es local y exploratoria. El control de origen y token no identifica usuarios ni separa propietarios de resultados. No es una plataforma multiusuario ni un despliegue público. Escuchar en loopback y desactivar las funciones cloud no equivale a aislar toda la red del equipo.

El simulador no lee archivos del host, no recibe SQL libre y no utiliza correo real. En consecuencia, los resultados no describen una integración con un sistema de correo, una base empresarial o una red de producción.

## Componentes pendientes

| Componente | Estado |
|---|---|
| Corpus final reservado por familias o escenarios | Pendiente |
| Evaluación completa de todos los efectos de una tarea | Pendiente; el hallazgo ya está documentado |
| Registro explícito de qué resultados observó cada turno | Pendiente |
| Control de flujo que exija observación antes de actuar | Propuesto, sin incorporar silenciosamente a C0 |
| Clasificador de inyección y C3 | No implementado |
| Aprobación de acciones y C4 | No implementado |
| Cola persistente y recuperación de trabajos | No implementadas |
| Motor de reglas SOC, expedientes e integración Wazuh | No implementados |
| Evaluación estadística final | Pendiente de cerrar diseño y obtener resultados |

Las mejoras futuras deben conservar versiones y criterios de comparación. Un control nuevo debe aparecer como tratamiento explícito o como una nueva arquitectura con su propia línea base. C2PO seguirá separado porque conoce el canario exacto.

Las evidencias publicadas y las exclusiones del paquete están inventariadas en [`evidence/README.md`](../evidence/README.md).
