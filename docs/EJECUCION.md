# Ejecutar el laboratorio

## Entorno

Python 3.10 o posterior. La versión comprobada localmente es 3.14.8 sobre Fedora 44. No se ha validado Kali, Windows o macOS. La ejecución sin modelo no necesita dependencias de terceros.

Todos los comandos parten de la carpeta que contiene `README.md`, `promptlab/`, `data/` y `tests/`. Ejecutarlos desde otra carpeta puede producir `No module named promptlab`.

```bash
python3 -m promptlab --help
python3 -m promptlab doctor
python3 -m promptlab inspect
```

`inspect` debe encontrar 36 casos: 24 ataques y 12 variantes benignas, todos en `dev`. `doctor` comprueba el entorno y el corpus; sin `--model` no hace solicitudes de red.

## Interfaz local

```bash
python3 -m promptlab ui
```

Abre [http://127.0.0.1:8765](http://127.0.0.1:8765) y conserva la terminal abierta. Ctrl+C cierra el servidor. Si el puerto está ocupado, utiliza `--port 8766` y entra al puerto indicado.

Para empezar, selecciona **Documento intervenido**, **Demo guiada** y **Comparar**. La demo fuerza las llamadas para mostrar permisos; no interpreta el texto ni ejecuta IA. **Resultado** muestra respuesta y buzón. **Línea de acciones** separa propuestas y resultados de herramientas.

**Modelo local** permite editar la petición y el texto adversarial. Los permisos y criterios siguen siendo los del escenario elegido. Una edición que cambie el objetivo de la tarea no constituye por sí sola una evaluación válida de una tarea nueva.

**Ejecuciones** abre los lotes de `results/`. Conserva los veredictos de la versión que los generó. El botón de descarga exporta el manifiesto y las pruebas como JSON.

## Ollama

Sigue la [instalación oficial](https://docs.ollama.com/linux) si no lo tienes. Para este laboratorio, el servidor debe permanecer en loopback. La variable que desactiva cloud se aplica al proceso del servidor, no solo a la terminal que ejecuta PromptLab.

Si Ollama funciona como servicio systemd, utiliza `sudo systemctl edit ollama.service` y añade:

```ini
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_NO_CLOUD=1"
```

Después recarga y reinicia el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama.service
```

Si no utilizas servicio, la alternativa es iniciar el servidor en una terminal dedicada:

```bash
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_NO_CLOUD=1 ollama serve
```

No inicies ambas modalidades a la vez. La [FAQ de Ollama](https://docs.ollama.com/faq) documenta estas variables. Loopback y cloud desactivado no certifican aislamiento de red de todo el equipo.

## Primer modelo y tareas benignas

El modelo utilizado en las evidencias es Qwen2.5:7b Q4_K_M. Se ejecutó sobre CPU; la velocidad depende del equipo. El repositorio no incluye pesos del modelo.

```bash
ollama pull qwen2.5:7b
ollama list
python3 -m promptlab doctor --model qwen2.5:7b
python3 -m promptlab run --model qwen2.5:7b --kind benign --configs C0 C2 C2P --limit-per-kind 3 --repeats 1
```

El diagnóstico debe mostrar `model_metadata_verified: true`. Su campo `inference_tested: false` describe al comando `doctor`: ese comando no pide generaciones, aunque ya existan lotes reales.

El piloto ejecuta tres tareas por configuración. Revisa tanto `legitimate_task_success` como los hechos y efectos del buzón. `status: completed` solo indica que terminó el ciclo.

El adaptador rechaza modelos remotos conocidos, exige capacidad de herramientas y verifica metadatos antes/después. Esas comprobaciones presuponen un servidor confiable.

## Demo por consola

```bash
python3 -m promptlab demo --configs C0 C1 C2 P C2P
```

Fuerza una escena adversarial por configuración y genera un informe identificado como **SIN LLM**. No ejecuta el corpus completo ni mide resistencia de prompts.

## Piloto adversarial de desarrollo

Este comando está disponible, pero no se ha ejecutado en los resultados publicados:

```bash
python3 -m promptlab run --model qwen2.5:7b --configs C0 C2 C2P --limit-per-kind 6 --repeats 1
```

Selecciona seis ataques y seis tareas benignas por configuración: 36 pruebas. El número de solicitudes al modelo será mayor por el ciclo de herramientas. Antes de interpretar seguridad, revisa exposición, utilidad, errores y criterios del evaluador.

## Archivos de una ejecución

Cada lote crea una carpeta nueva en `results/`:

| Archivo | Contenido |
|---|---|
| `manifest.json` | Versión, modelo, parámetros, hashes y estado del lote |
| `cases_used.jsonl` | Casos exactos empleados |
| `trials.jsonl` | Mensajes observables, herramientas, decisiones, buzón y veredictos |
| `events.jsonl` | Vista de decisiones de herramientas con referencias de orden |
| `SUMMARY.md`, `summary.csv`, `summary.json` | Conteos y métricas descriptivas |

La consola baraja el orden con semilla; la comparación visual ejecuta C0 y después C2P. Los lotes visuales se marcan exploratorios.

El código de salida 2 señala errores, límites, interrupción o identidad de modelo no verificada; no significa que un ataque haya tenido éxito. Ctrl+C conserva lo ya registrado por la consola. La interfaz espera la llamada activa al cancelar y descarta sus propuestas; no revierte efectos anteriores.
