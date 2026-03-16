# Herramientas ADA v2/v3 — Para qué sirven

En la Web Admin, en el chat, puedes desplegar **Herramientas ADA (v2/v3)**. Cada botón llama a una API del agent-core y te muestra el resultado. Resumen de uso:

---

## Objetivos (v2)

- **Qué hace:** Lista los objetivos activos que ADA tiene en memoria (los que el scheduler y los motores usan para generar ideas y oportunidades).
- **Para qué:** Ver en qué está trabajando ADA en segundo plano. Si no hay objetivos, el scheduler no tiene “temas” sobre los que generar ideas.

---

## Añadir objetivo (v2)

- **Qué hace:** Añade un nuevo objetivo (texto libre). ADA lo guarda y el scheduler puede generar ideas y oportunidades a partir de él.
- **Para qué:** Darle a ADA un foco claro (ej. “aumentar ingresos con un producto digital”, “mejorar la visibilidad del proyecto”). Sin objetivos añadidos, no hay “combustible” para oportunidades y planes.

---

## Investigar (v3)

- **Qué hace:** Envía un tema de investigación al motor de investigación (research_engine + reasoning). Devuelve análisis y estrategias en texto.
- **Para qué:** Pedir a ADA que analice un tema concreto (ej. “cómo monetizar un blog”, “qué canales usar para vender”) sin tener que escribirlo en el chat. Útil para obtener un informe rápido y luego seguir la conversación.

---

## Auto-mejora (v2)

- **Qué hace:** Ejecuta el análisis de cuellos de botella del sistema (self_improvement_engine) y devuelve sugerencias de mejora.
- **Para qué:** Revisar qué podría estar limitando a ADA (configuración, recursos, flujos) y qué mejorar. Es un “diagnóstico” del propio sistema.

---

## Oportunidades (v3)

- **Qué hace:** Lista las oportunidades mejor puntuadas (ideas evaluadas por opportunity_engine que el scheduler fue guardando).
- **Para qué:** Ver qué acciones o ideas ADA considera más valiosas en este momento. Puedes usarlas para decidir en qué trabajar o qué aprobar.

---

## Planes (v3)

- **Qué hace:** Lista los planes de acción generados (por el scheduler / strategy_engine a partir de oportunidades).
- **Para qué:** Ver los pasos concretos que ADA ha propuesto. Complementa al “plan” clásico del chat: aquí ves la salida más estructurada del motor de planes (v3).

---

## Aprendizaje (v3)

- **Qué hace:** Lista aprendizajes recientes (experiencias con evaluación o aprendizaje guardadas en memoria).
- **Para qué:** Ver qué ha “aprendido” ADA de ejecuciones o decisiones recientes. Útil para revisar si el sistema está refinando su criterio con el uso.

---

## Resumen rápido

| Botón          | Uso típico |
|----------------|------------|
| Objetivos      | Ver en qué está trabajando ADA. |
| Añadir objetivo | Dar un foco (ingresos, visibilidad, etc.) para que genere ideas y planes. |
| Investigar     | Obtener análisis y estrategias sobre un tema concreto. |
| Auto-mejora    | Revisar cuellos de botella y sugerencias de mejora del sistema. |
| Oportunidades  | Ver las ideas/acciones mejor puntuadas. |
| Planes         | Ver los planes de acción generados por ADA. |
| Aprendizaje    | Ver qué ha aprendido ADA de experiencias recientes. |

---

## Archivos: ¿simula o ejecuta?

**ADA ejecuta las operaciones de archivo de verdad** (no las simula): escribe y lee en disco con `WRITE_FILE`, `READ_FILE`, `LIST_DIR`, etc.

Para **crear o editar archivos en el directorio que asignaste** (p. ej. `/Volumes/Datos/dockers`), hay que usar en el chat rutas con el prefijo **`dockers/`**:

- Ejemplo: *"Crea el archivo dockers/mi-proyecto/README.md con el contenido..."*
- Listar: *"Lista dockers"* o *"Lista dockers/mi-proyecto"*
- Leer: *"Lee dockers/mi-proyecto/package.json"*

Sin el prefijo `dockers/`, ADA escribe en el **workspace** del propio proyecto ADA (repo actual). Con `dockers/` escribe en la carpeta de proyectos montada (la que ves en ARCHIVOS en la interfaz). La variable `ENABLE_AGENT_FS=1` en la interfaz permite además crear/editar archivos desde la UI en esa misma raíz.

**Planes con WRITE_FILE:** Si ADA propone un plan que solo incluye acciones de archivo (crear/leer/listar/buscar), el plan se **ejecuta automáticamente** y los archivos se crean sin tener que pulsar «Ejecutar plan». Si el plan incluye comandos (RUN_COMMAND) o borrados (DELETE), sigue pidiendo aprobación. El cierre del contenido de un archivo puede ser `END_FILE` o `**END_FILE**`.
