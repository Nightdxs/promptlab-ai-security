# Pruebas y reproducción

La suite actual contiene 75 pruebas de software. Utiliza respuestas programadas, fixtures ficticios y servidores HTTP temporales en loopback. No instala Ollama, no descarga modelos y no pide generaciones a un LLM real.

## Ejecutar

Desde la raíz del repositorio:

```bash
python3 -m unittest discover -s tests -v
python3 -m promptlab inspect
python3 -m scripts.reproduce_findings --expect-fixed
python3 tools/verify_evidence.py
```

La suite debe terminar con `Ran 75 tests` y `OK`. El log local conservado está en [`unit-tests.txt`](../evidence/software/unit-tests.txt) y el entorno y comando en [`validation.json`](../evidence/software/validation.json).

## Cobertura funcional

| Archivo | Qué comprueba |
|---|---|
| `test_lab.py` | Herramientas, fixtures, permisos, presupuestos, evaluador, selección y reportes |
| `test_audit.py` | Respuestas mal formadas o truncadas, evidencia de tarea, exposición y separación de controles |
| `test_integration.py` | Ciclo HTTP completo, alias remoto e identidad de modelo cambiante, usando un servidor programado |
| `test_readiness.py` | Diagnóstico, selección benigna, exportación de eventos y regresión sobre contenido del correo |
| `test_web.py` | Host/origen/token, entradas, comparación guiada, ediciones, concurrencia, identidad y cancelación |

La cancelación se prueba con una respuesta pendiente que contiene una llamada de herramienta. Al cancelar, la propuesta se descarta; los efectos anteriores no se revierten. La regresión del correo distingue un nombre en el saludo, una responsable incorrecta y una línea correcta del fixture.

El número de tests no es una cobertura porcentual ni un número de ataques evaluados. No se incluye un informe de cobertura de líneas.

## Regresiones reproducibles

`scripts.reproduce_findings` ejecuta seis comprobaciones controladas del adaptador y el evaluador. Su salida se conserva en [`regressions.json`](../evidence/software/regressions.json). Son reproducciones de software; no requieren un modelo.

## Integridad de las evidencias

`tools/verify_evidence.py` comprueba hashes, estados, fuentes y los conteos de los pilotos publicados. La validación local también comprobó el caso negativo: una copia alterada de una traza se rechaza. La alteración se realizó en una carpeta temporal; las evidencias originales no se modificaron. Véase [`integrity-check.json`](../evidence/software/integrity-check.json).

Se exportaron además los archivos en staging a una carpeta limpia con `git checkout-index` y se verificó de nuevo la evidencia. El CSV muestreado conserva los mismos bytes en el directorio de trabajo y en el índice de Git. El registro está en [`git-checkout.json`](../evidence/software/git-checkout.json).

## JavaScript e interfaz

El archivo de la interfaz se comprueba sintácticamente con:

```bash
node --check promptlab/web_assets/app.js
```

Node es opcional para esta comprobación, no un requisito de ejecución de PromptLab. La UI ya se verificó en navegador con comparación guiada, consulta real con Ollama, apertura de historial y aviso de correos adicionales. El registro está en [`interface-checks-20261027.json`](../evidence/software/interface-checks-20261027.json); la consulta real conserva su [lote completo](../evidence/runs/05-ui-lookup-0.3.0/).

## CI

El flujo [`tests.yml`](../.github/workflows/tests.yml) prepara Python 3.10 y 3.14 en Ubuntu y ejecuta tests, validación del corpus, regresiones e integridad. Tiene permisos de lectura de contenidos y no utiliza claves de API ni un modelo.

Las acciones oficiales se fijaron a los commits devueltos por las referencias consultadas el 27/10/2026. Su procedencia se conserva en [`ci-action-refs.json`](../evidence/software/ci-action-refs.json). Referencias: [actions/checkout](https://github.com/actions/checkout) y [actions/setup-python](https://github.com/actions/setup-python).

El flujo aún no tiene una ejecución verificada en GitHub. El resultado local de Python 3.14.8 y el futuro resultado de la matriz de CI son evidencias distintas.
