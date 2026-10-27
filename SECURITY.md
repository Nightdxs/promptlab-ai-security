# Alcance del laboratorio

PromptLab 0.3.0 está preparado para pruebas locales con datos ficticios. No es un sistema de producción ni una plataforma multiusuario.

Las herramientas del agente no exponen shell, SQL libre, lectura de rutas del host o SMTP. El servidor y el adaptador utilizan loopback. Los metadatos de Ollama se verifican bajo el supuesto de que ese servidor es confiable; estas comprobaciones no certifican aislamiento del equipo.

Para describir un fallo, usa un caso reproducible con datos ficticios y diferencia propuesta, ejecución y efecto. Incluye versión, configuración, entrada, resultado esperado y archivo de evidencia. Una reproducción con respuestas programadas debe identificarse como tal.

No publiques credenciales, documentos personales o registros de terceros en un informe. El repositorio conserva solo la selección descrita en [`evidence/README.md`](evidence/README.md).
