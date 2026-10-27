# Roadmap

La versión actual es 0.3.0. Esta lista describe trabajo pendiente; no se cuenta como funcionalidad implementada.

## Evaluación de tareas

- Definir contratos por escenario: hechos, recursos, destinatarios y cantidad de efectos permitidos.
- Separar cumplimiento mínimo y completo.
- Detectar correos adicionales o incorrectos aunque exista otro correcto.
- Registrar qué resultados había observado el modelo antes de proponer cada acción.
- Evaluar un control de flujo separado que exija esa observación antes de actuar. Si cambia la arquitectura común, generar una nueva línea base.

Criterio de salida: los casos documentados en `docs/casos/` se reproducen y reciben el veredicto esperado sin cambiar los informes históricos.

## Ejecución persistente

- Cola común para web y consola.
- Trabajos y eventos duraderos.
- Cancelación y recuperación tras reinicio.
- Presupuestos de tiempo, llamadas y almacenamiento.
- Respaldo y restauración probados.

Criterio de salida: un reinicio no pierde las evidencias ni convierte una interrupción en una tarea correcta o un ataque bloqueado.

## Investigación de eventos

- Esquema común de eventos con referencias a turno, llamada, decisión y efecto.
- Reglas para accesos fuera de permiso, efectos adicionales y acciones sin observación previa.
- Alertas enlazadas a evidencias y casos de investigación.
- Exportación JSONL para una integración SIEM posterior.

Criterio de salida: cada alerta tiene un caso positivo, uno negativo y una explicación verificable. La exportación preparada se distingue de una integración comprobada.

## Evaluación académica

- Escenarios y tareas distintas de las variantes actuales.
- Partición final reservada por familias o escenarios.
- Configuraciones, verificadores y protocolo congelados.
- Clasificador y aprobación de acciones como tratamientos explícitos, si se mantienen en el alcance.
- Lotes reales, revisión de casos ambiguos y análisis que respete el emparejamiento.

Criterio de salida: resultados trazables y limitaciones explícitas, aunque la hipótesis no se cumpla. La ausencia de un ataque exitoso no se sustituye por una demo presentada como evaluación real.

## Instalación local estable

- Una fuente principal de código y releases identificadas.
- Configuración y datos separados del código.
- Servicio local y acceso directo al navegador.
- Prueba desde una copia limpia y restauración de un respaldo.

La primera instalación estable puede entregarse antes de completar la investigación. La portabilidad a Kali y la integración Wazuh necesitan sus propias comprobaciones.
