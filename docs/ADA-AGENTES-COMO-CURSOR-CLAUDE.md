# ADA con capacidades tipo Cursor / Claude (agentes que manipulan archivos y el sistema)

¿Se puede hacer que ADA haga lo mismo que en Cursor con sus agentes, o que Claude manipule el ordenador o los archivos cuando haga falta? **Sí es posible.** ADA ya hace parte de eso; el resto es ampliar herramientas y, si quieres, ejecución de comandos con controles de seguridad.

---

## 1. Qué hace hoy ADA (sin salir del chat)

- **Leer archivos del proyecto:** Si en la respuesta del modelo aparece una línea `READ_FILE: ruta/archivo`, el sistema **lee de verdad** ese archivo (dentro del workspace) y devuelve el contenido al modelo para la siguiente ronda.
- **Escribir archivos del proyecto:** Si aparece `WRITE_FILE: ruta/archivo` y luego el contenido y `END_FILE`, el sistema **escribe de verdad** en ese archivo.
- El **workspace** es la carpeta del proyecto (en Docker suele ser `.:/workspace`). Todo es relativo a esa raíz.

Es decir: ADA **ya puede** manipular archivos del repo cuando el LLM “decide” usar esas instrucciones en su respuesta. No es simulación: lee y escribe en disco.

---

## 2. Qué hacen Cursor y Claude que aquí aún no está

| Capacidad | Cursor / Claude | ADA hoy |
|-----------|------------------|--------|
| Leer archivos | ✅ | ✅ (READ_FILE) |
| Escribir archivos | ✅ | ✅ (WRITE_FILE) |
| Listar / explorar carpetas | ✅ | ❌ |
| Buscar en el código (grep/search) | ✅ | ❌ |
| Ejecutar comandos en terminal | ✅ | ❌ |
| Editar por fragmentos (search/replace) | ✅ | Solo archivo completo (WRITE_FILE) |
| Varias herramientas en un turno | ✅ | ✅ (varias líneas READ_FILE/WRITE_FILE) |

Para acercar ADA a ese comportamiento haría falta:

- **Listar directorios** (ej. `LIST_DIR: ruta`) para que pueda explorar el proyecto.
- **Buscar en archivos** (ej. `SEARCH: patrón` o `GREP: patrón`) para encontrar código o texto.
- **Ejecutar comandos** (ej. `RUN_COMMAND: comando`) con **reglas de seguridad**: lista blanca de comandos, o pedir confirmación humana para comandos “peligrosos”, o ejecutar en un contenedor/sandbox.

---

## 3. Cómo hacerlo técnicamente (sin cambiar de stack)

- **Mismo esquema que ahora:** el modelo (Ollama/Gemini) no tiene “tool calls” estructurados; escribe en su respuesta líneas especiales que agent-core interpreta.
- Se pueden añadir más “verbos” al mismo estilo:
  - `LIST_DIR: ruta` → agent-core lista ese directorio y devuelve el resultado al modelo.
  - `SEARCH: patrón` o `GREP: patrón [ruta]` → agent-core busca (p. ej. con `grep` o buscando en archivos) y devuelve el resultado.
  - `RUN_COMMAND: comando` → agent-core ejecuta el comando (en el host o en un contenedor) y devuelve stdout/stderr. **Aquí es donde hay que definir la política de seguridad.**

Con eso, ADA podría:

- Explorar el proyecto (LIST_DIR).
- Encontrar dónde está algo (SEARCH/GREP).
- Leer y editar archivos (ya lo hace).
- Ejecutar scripts o comandos (RUN_COMMAND) si tú lo permites y cómo lo permites.

---

## 4. Seguridad si se añade ejecución de comandos

- **Listar y buscar** son de bajo riesgo si se limitan al workspace.
- **Ejecutar comandos** puede ser peligroso. Opciones razonables:
  - **Lista blanca:** solo permitir comandos predefinidos (ej. `npm run build`, `python -m pytest`, `ollama list`).
  - **Aprobación humana:** comandos no permitidos se muestran en la UI y el usuario tiene que aprobar antes de ejecutar (similar a las propuestas pendientes).
  - **Sandbox:** ejecutar en un contenedor o entorno restringido (solo ciertas carpetas, sin red, etc.).

Así ADA podría “manipular el ordenador o los archivos cuando haga falta” de forma controlada, como un agente tipo Cursor/Claude pero con las reglas que tú definas.

---

## 5. Resumen

- **¿Es posible que ADA haga lo mismo que con Cursor y sus agentes, o que Claude manipule archivos/sistema?** Sí: en parte ya lo hace (lectura/escritura de archivos en el proyecto) y el resto es ampliar el conjunto de herramientas.
- **Qué ya tiene:** leer y escribir archivos en el workspace desde el chat.
- **Qué se puede añadir:** listar directorios, buscar en archivos y, con cuidado, ejecutar comandos (con lista blanca, aprobación humana y/o sandbox).

---

## 6. Implementado (agent-core)

Ya están implementadas en agent-core:

- **LIST_DIR: ruta** — Lista el contenido del directorio (rutas relativas al workspace). Respuesta con `DIR`/`FILE` y nombres.
- **GREP: patrón [ruta]** — Busca el patrón en archivos (regex); opcionalmente limita a una carpeta. Ignora `node_modules`, `.git`, `__pycache__`. Máximo ~150 coincidencias.
- **RUN_COMMAND: comando** — Ejecuta el comando en la raíz del workspace **solo si**:
  - `ADA_ALLOW_RUN_COMMAND=true` en el entorno de agent-core.
  - El primer token del comando está en la lista blanca (por defecto: `ls`, `cat`, `npm`, `node`, `python`, `git`, `grep`, `find`, etc.).
  - No se permiten `rm`, `sudo`, `dd`, etc. (bloqueados por seguridad).

Variables opcionales en `.env` o en `environment` de agent-core:

- `ADA_ALLOW_RUN_COMMAND=true` — Activa la ejecución de comandos.
- `ADA_RUN_COMMAND_ALLOWLIST=npm,node,python,...` — Lista de comandos permitidos (primer token). Si no se define, se usa la lista por defecto.
- `ADA_RUN_COMMAND_TIMEOUT=60` — Timeout en segundos (por defecto 60).

En el chat, ADA puede usar estas líneas en su respuesta y el sistema las ejecuta e inyecta el resultado en la siguiente ronda del LLM.
