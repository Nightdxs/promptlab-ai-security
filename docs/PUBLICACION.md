# Preparar la subida a GitHub

El paquete contiene código, pruebas, documentación y una selección de evidencias. No incluye pesos del modelo, resultados nuevos de trabajo, el PDF académico personal ni credenciales. La carpeta `results/` está excluida de Git; las evidencias revisadas están en `evidence/`.

## Antes del primer commit

Desde la carpeta del proyecto:

```bash
python3 tools/verify_evidence.py
git init -b main
git add .
git status
git diff --cached --stat
```

La copia local preparada puede tener ya el repositorio inicializado y los archivos en staging. El ZIP no contiene `.git`, por lo que al descomprimirlo se inicia un repositorio nuevo. No se ha creado un historial de commits ni se han puesto fechas anteriores.

Revisa los archivos que entrarán en el commit. Los atributos de Git conservan los bytes de las evidencias; no normalices esos archivos con un editor. Los comandos de ejecución parten de la carpeta del README.

## Repositorio remoto

Crea o selecciona un repositorio vacío en tu cuenta y utiliza su URL real. El proyecto no tiene un propietario o remoto preconfigurado.

Después de revisar el contenido y utilizar tu configuración de autor en Git:

```bash
git commit -m "Documentar PromptLab y sus evidencias"
```

Para introducir la URL sin dejar un usuario ficticio en el comando:

```bash
read -r -p "URL de tu repositorio: " promptlab_repo_url
git remote add origin "$promptlab_repo_url"
git push -u origin main
```

Si ese repositorio ya tiene contenido o un remoto configurado, revisa su historia y ramas antes de aplicar estos pasos. Este procedimiento parte de una copia nueva con un remoto vacío.

## Después de subir

- Abre el README y comprueba imagen y enlaces.
- Revisa Actions: el workflow está configurado, pero no se entrega como una ejecución ya aprobada en GitHub.
- Consulta los logs de cada versión de Python. El resultado local de 75 tests y el resultado del workflow son comprobaciones distintas.
- Añade una descripción breve del repositorio, por ejemplo: `Laboratorio local de seguridad de agentes de IA con herramientas simuladas, trazas y evaluación reproducible.`

La elección de una licencia queda pendiente del autor; este paquete no incluye `LICENSE`. Las referencias técnicas están en [REFERENCIAS.md](REFERENCIAS.md). La documentación evita atribuir resultados o funciones que todavía no existen.
