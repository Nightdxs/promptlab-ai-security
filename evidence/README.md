# Evidencias incluidas

Este directorio conserva cinco lotes de desarrollo del 27 de octubre de 2026. Los manifiestos, casos usados, trazas y resúmenes se copiaron sin cambiar sus bytes. El índice está en [`INDEX.json`](INDEX.json) y sus hashes en [`SHA256SUMS`](SHA256SUMS).

## Lotes

| Directorio | Tipo | Estado | Qué permite revisar |
|---|---|---|---|
| [01-benign-0.2.1](runs/01-benign-0.2.1/) | LLM local, tareas benignas | 9/9 ejecuciones guardadas | Omisión de la responsable en los correos; seis mínimos cumplidos |
| [02-partial-0.2.2](runs/02-partial-0.2.2/) | LLM local, tareas benignas | 4/9 ejecuciones guardadas; interrumpido | Nombre en el saludo y límites del verificador mínimo |
| [03-benign-0.2.3](runs/03-benign-0.2.3/) | LLM local, tareas benignas | 9/9 ejecuciones guardadas | Nueve mínimos acreditados y un correo adicional con datos inventados |
| [04-guided-0.3.0](runs/04-guided-0.3.0/) | Demo programada, sin LLM | 2/2 ejecuciones guardadas | Misma secuencia fija en C0 y C2P; efecto del control de permisos |
| [05-ui-lookup-0.3.0](runs/05-ui-lookup-0.3.0/) | LLM local, consulta desde interfaz | 1/1 ejecución guardada | Consulta a SQLite y respuesta con identidad del modelo verificada |

Los campos `synthetic_no_llm` y `model_identity_verified` permiten distinguir el origen de cada lote. Un lote incompleto no representa las pruebas que faltan. Estas evidencias no incluyen el corpus adversarial ejecutado contra el LLM real.

## Archivos de cada lote

- `manifest.json`: versión, parámetros, identidad de modelo, hashes y estado.
- `cases_used.jsonl`: entrada exacta de cada caso evaluado.
- `trials.jsonl`: mensajes observables, llamadas, decisiones, respuesta y buzón.
- `events.jsonl`: decisiones de herramientas y referencia de orden dentro del lote.
- `summary.json`, `summary.csv`, `SUMMARY.md`: resúmenes originales.
- `source_snapshot/`: fuente de la versión indicada y corpus utilizado. Los tres primeros snapshots también conservan los archivos auxiliares disponibles. Los dos lotes de interfaz incluyen el paquete Python identificado por el manifiesto y el corpus; no se presentan como una copia completa de su entorno.

El registro no publica razonamiento interno del modelo. Los documentos, destinatarios `.invalid` y canarios son ficticios. No se incluyen los pesos de Ollama, el PDF académico con datos personales, rutas personales del equipo ni carpetas de trabajo.

La selección fue revisada buscando rutas personales, el identificador académico del documento de partida y patrones comunes de credenciales. No se encontraron coincidencias de esos patrones. Esa revisión no equivale a una auditoría independiente de seguridad. Los metadatos técnicos de versión, sistema, parámetros y horarios permanecen porque describen las condiciones de ejecución.

## Revisión adicional

[`reviews/pilot-review.json`](reviews/pilot-review.json) contiene la revisión posterior del piloto 0.2.3. Conserva el campo `reviewer: assistant_manual_review` y la marca `posthoc_diagnostic: true`. No se presenta como juicio humano independiente ni reemplaza los veredictos automáticos del lote.

## Validación del software

En [`software/`](software/) se guardan el log de la suite, los metadatos de su ejecución y las comprobaciones auxiliares. Los registros de software no son pruebas de resistencia de un LLM. La comprobación de interfaz de 2026-10-27 referencia por separado una consulta real y la demo programada.

El flujo de GitHub Actions se entrega configurado. No hay una ejecución de CI en GitHub acreditada por estos archivos.

## Comprobar integridad

Desde la raíz del repositorio:

```bash
python3 tools/verify_evidence.py
```

El comando comprueba el inventario de archivos, sus hashes, los snapshots y los conteos documentados. Devuelve 0 si coinciden y 1 si falta un archivo, cambia un hash o una condición no se cumple. No realiza inferencia ni solicitudes de red.

Los atributos de Git desactivan la normalización de texto dentro de `evidence/` para conservar los bytes originales. Esto importa para CSV con finales de línea CRLF. Los checksums detectan cambios respecto a esta selección; no prueban por sí solos la autenticidad de un servidor ni constituyen una firma de un tercero.

Para reproducir un lote histórico hay que utilizar su snapshot y sus parámetros. Ejecutarlo con el código actual no reproduce automáticamente la versión anterior. El motor, la cuantización y el equipo pueden producir salidas diferentes incluso con semilla fija.
