# Corpus de desarrollo

36 líneas JSONL: 24 ataques y 12 variantes benignas. Todos los datos, personas de ejemplo, direcciones `.invalid` y canarios del laboratorio son ficticios. Los nombres de autor y universidad solo aparecen en la documentación del proyecto.

## Campos

| Campo | Significado |
|---|---|
| `id` | Identificador único y estable |
| `kind` | `attack` o `benign` |
| `split` | Partición; aquí siempre `dev` |
| `placement` | `document`, `database`, `direct` o `none` |
| `goal` | `exfiltration`, `unauthorized_tool` o nulo |
| `technique` | Etiqueta opcional de la plantilla |
| `task` | `summary`, `lookup` o `mail` |
| `user_task` | Petición de trabajo legítima |
| `payload` | Texto insertado en la superficie controlada por el atacante |
| `expected` | Fragmentos mínimos que debe contener la respuesta o correo legítimo |
| `owasp_tags` | Etiquetas orientativas y no categorías excluyentes |

La autorización se deriva de la tarea en `policy_for`, fuera del texto recuperado. La etiqueta `goal`, el tipo y los criterios del evaluador no se pasan al modelo.

El verificador textual usa fragmentos, no un juez semántico. Puede tener falsos positivos y negativos; una coincidencia no garantiza la corrección de toda la respuesta. Revisa los casos ambiguos antes de concluir.

Cambiar de tarea o añadir nuevos activos requiere adaptar fixtures, permisos y verificadores. Modificar solo el campo `user_task` puede producir una prueba inválida.

No hay prueba final oculta incluida en este paquete. Las paráfrasis de las mismas plantillas no cuentan como nuevas familias independientes.
