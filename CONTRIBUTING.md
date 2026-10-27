# Cambios y reproducción

Antes de modificar una defensa o el evaluador, conserva el caso que motivó el cambio y describe el resultado esperado. Incluye una prueba de regresión cuando se corrija un comportamiento del motor o del verificador.

```bash
python3 -m unittest discover -s tests -v
python3 -m scripts.reproduce_findings --expect-fixed
python3 tools/verify_evidence.py
```

Para documentar un fallo, indica comando, versión, caso, configuración, efecto observado y archivo de evidencia. Distingue un error de ejecución, una tarea incompleta y una violación de política. No hace falta que una prueba con el modelo tenga un ataque exitoso para que el informe sea útil.

No ajustes una defensa después de ver el conjunto final y sigas llamando desconocido a ese conjunto. Los cambios de prompt, política, herramienta o evaluación deben quedar versionados. Los resultados históricos no se reemplazan por los de la última versión.

La suite usa datos y respuestas controladas. Los lotes con un LLM se ejecutan por separado y conservan sus propios manifiestos. Una captura puede acompañar un resultado, pero no sustituye la traza.

Los textos de la documentación deben describir hechos y decisiones comprobables. Evita atribuir a una defensa lo que no aisló el experimento o presentar planes como funciones disponibles.
