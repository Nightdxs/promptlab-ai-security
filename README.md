# PromptLab

Laboratorio local para estudiar cómo un agente de IA utiliza herramientas cuando recibe instrucciones dentro de documentos o registros. Registra las llamadas propuestas, las decisiones de autorización y los efectos producidos en un entorno con datos ficticios.

El proyecto usa Python, SQLite y Ollama. Las herramientas leen documentos de prueba, consultan registros y escriben en un buzón simulado. No acceden a archivos del equipo ni envían correo real.

**Estado: v0.3.0, en desarrollo.** Hay pruebas de software, una demo programada y pilotos benignos con Qwen2.5:7b. La evaluación del corpus de ataques con el modelo real sigue pendiente.

![Comparación local entre C0 y C2P en la demo programada](docs/img/interfaz.png)

## Probarlo

Necesita Python 3.10 o posterior. El programa y sus pruebas usan la biblioteca estándar; no hay paquetes Python que instalar. El entorno comprobado es Fedora 44 con Python 3.14.8.

Abre una terminal en la carpeta que contiene este README:

```bash
python3 -m promptlab doctor
python3 -m unittest discover -s tests -v
python3 -m promptlab ui
```

Entra a [http://127.0.0.1:8765](http://127.0.0.1:8765). Selecciona **Documento intervenido → Demo guiada → Comparar → Ejecutar prueba**. En esta demo las acciones están fijadas: sirve para seguir el control de permisos, no para medir la vulnerabilidad de un modelo.

Para usar un LLM necesitas Ollama y un modelo local con llamadas de herramientas. El modelo utilizado en los pilotos incluidos es `qwen2.5:7b`:

```bash
ollama pull qwen2.5:7b
python3 -m promptlab doctor --model qwen2.5:7b
python3 -m promptlab run --model qwen2.5:7b --kind benign --configs C0 C2 C2P --limit-per-kind 3 --repeats 1
```

La [guía de ejecución](docs/EJECUCION.md) explica la configuración local de Ollama, la interfaz y los archivos de salida.

## Qué se puede observar

- Si el modelo consulta la fuente necesaria para una tarea.
- Qué herramientas propone y cuáles se ejecutan o bloquean.
- Si aparece un canario ficticio en una salida instrumentada.
- Si la tarea cumple los criterios mínimos y qué efectos adicionales deja.
- Cómo cambia la misma prueba entre configuraciones.

La consola permite ejecutar lotes. La interfaz sirve para explorar un caso, editar sus textos y revisar resultados anteriores. Las ediciones visuales conservan los permisos y criterios del escenario original.

## Resultados disponibles

El piloto de v0.2.3 contiene tres tareas conocidas —resumen, consulta y correo— evaluadas en tres configuraciones. Son nueve ejecuciones, no nueve tareas independientes.

| Configuración | Cumplimiento mínimo automático | Revisión posterior de los efectos |
|---|---:|---:|
| C0 | 3/3 | 2/3 |
| C2 | 3/3 | 3/3 |
| C2P | 3/3 | 3/3 |

C0 registró un correo con datos inventados y después otro correcto. El segundo acreditó el mínimo, pero no eliminó el primero. La revisión adicional fue realizada por el asistente después de la ejecución y se conserva separada de los veredictos automáticos.

Este resultado muestra un límite del agente y de la métrica. No es una prueba de inyección de prompt ni demuestra eficacia general de las defensas. Los [resultados y sus condiciones](docs/RESULTADOS.md) enlazan a las trazas completas.

## Pruebas y evidencias

La suite contiene **75 pruebas de software**. Comprueba el motor, permisos, informes, contrato HTTP e interfaz con respuestas controladas. No descarga ni ejecuta un LLM.

```bash
python3 -m unittest discover -s tests -v
python3 -m scripts.reproduce_findings --expect-fixed
python3 tools/verify_evidence.py
```

En [`evidence/`](evidence/README.md) están los lotes seleccionados, manifiestos, código de cada versión, revisión adicional y registro de validación. El verificador comprueba los hashes y la coherencia básica de los resultados. Los hashes permiten detectar cambios respecto al paquete; no sustituyen una validación independiente.

El flujo de GitHub Actions está configurado para Python 3.10 y 3.14. Sus ejecuciones en GitHub se comprobarán después de subir el repositorio; el registro incluido corresponde a pruebas locales. Véase [PRUEBAS.md](docs/PRUEBAS.md).

## Documentación

| Documento | Contenido |
|---|---|
| [Ejecución](docs/EJECUCION.md) | Diagnóstico, demo, modelo real e interfaz |
| [Arquitectura](docs/ARQUITECTURA.md) | Componentes, herramientas y fronteras de confianza |
| [Metodología](docs/METODOLOGIA.md) | Corpus, configuraciones, veredictos y métricas |
| [Resultados](docs/RESULTADOS.md) | Pilotos incluidos y enlaces a los registros |
| [Pruebas](docs/PRUEBAS.md) | Comandos de validación y cobertura de la suite |
| [Casos de estudio](docs/casos/01-correo-sin-observacion.md) | Análisis de fallos observados |
| [Limitaciones](docs/LIMITACIONES.md) | Qué no cubre todavía el laboratorio |
| [Roadmap](ROADMAP.md) | Mejoras propuestas y criterios de salida |

El corpus es de desarrollo. No hay todavía una partición final independiente, integración con un SIEM, clasificador de inyección ni aprobación de acciones. El proyecto sigue en fase de validación de su agente y sus criterios de evaluación.
