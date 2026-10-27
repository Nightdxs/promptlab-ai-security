# Publicación y comprobaciones

El repositorio público es [Nightdxs/promptlab-ai-security](https://github.com/Nightdxs/promptlab-ai-security). Contiene código, pruebas, documentación y evidencias seleccionadas. Los pesos del modelo, archivos personales y resultados nuevos de trabajo no forman parte del repositorio.

## Obtener una copia

```bash
git clone https://github.com/Nightdxs/promptlab-ai-security.git
cd promptlab-ai-security
python3 tools/verify_evidence.py
```

Clonar conserva el historial real de GitHub. Los paquetes ZIP no incluyen `.git`; no son una copia del historial. Para ejecutar el programa, sigue [EJECUCION.md](EJECUCION.md).

## Comprobaciones realizadas

- El README y la captura se publicaron junto con el código.
- Se descargó una copia desde GitHub y se verificaron sus evidencias.
- GitHub Actions pasó con Python 3.10 y 3.14, con 75 pruebas en cada versión.
- El commit y los jobs comprobados se conservan en [github-ci.json](../evidence/software/github-ci.json).

Los metadatos de CI identifican el commit que validaron. Los registros locales anteriores permanecen intactos y no se sustituyen por los de GitHub.

## Cambios posteriores

Antes de enviar cambios:

```bash
python3 -m unittest discover -s tests -v
python3 -m scripts.reproduce_findings --expect-fixed
python3 tools/verify_evidence.py
git status
git diff
```

No reemplaces las trazas de un lote por las de una ejecución nueva. Para añadir evidencia, conserva su origen y actualiza el índice y los checksums de forma explícita. El directorio `results/` sigue excluido de Git; la selección revisada está en `evidence/`.

La elección de una licencia queda pendiente del autor; el repositorio no incluye `LICENSE`. Las referencias técnicas están en [REFERENCIAS.md](REFERENCIAS.md).
