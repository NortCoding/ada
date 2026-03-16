# Qué es real y qué es simulación cuando interactúas con ADA

Respuesta directa: **no todo es simulación**. ADA puede trabajar en parte como un Claude: conversación real, lectura/escritura de archivos del proyecto, memoria y finanzas reales. Otras partes (ejecución de tareas “en el mundo”) pasan por un pipeline real pero con efectos limitados o que requieren aprobación.

---

## 1. Resumen rápido

| Qué hace ADA | ¿Real o simulado? | Notas |
|--------------|-------------------|--------|
| **Conversación (chat)** | **Real** | Ollama o Gemini generan la respuesta. No es simulado. |
| **Leer y escribir archivos del proyecto** | **Real** | Si `ADA_WORKSPACE` está definido (ej. `.:/workspace`), ADA puede usar READ_FILE y WRITE_FILE y el sistema **realmente** lee/escribe en tu repo. Como Claude editando código. |
| **Memoria (planes, contexto)** | **Real** | memory-db persiste; los planes y datos están guardados de verdad. |
| **Finanzas (balance, ledger)** | **Real** | financial-ledger es una API real; lo que ADA lee o registra ahí es persistente. |
| **Simulación de ROI/riesgo** | **Simulación por diseño** | simulation-engine calcula impacto/ROI/riesgo para que la política decida; no ejecuta nada en el mundo. |
| **Política (aprobar o no)** | **Real** | policy-engine aplica reglas reales (BD). Puede devolver `simulated_approval` para auto-aprobar en pruebas. |
| **Ejecución de tareas (task-runner)** | **Pipeline real, efectos limitados** | Se llama a task-runner de verdad, pero hoy **no** tiene integraciones reales (Gumroad, envío de emails, etc.): devuelve éxito y registra en logs. Para que “trabaje como Claude” en acciones del mundo hace falta añadir esas integraciones. |
| **Compras / gastos** | **Suelen pedir aprobación humana** | Por defecto no se ejecutan hasta que apruebas en Web-Admin (o con política `simulated_approval` / `ADA_AUTONOMOUS_PURCHASES`). |

---

## 2. Dónde ADA se parece a Claude (real)

- **Razonamiento y texto:** Mismo modelo (Ollama/Gemini) que usa un asistente; la conversación es real.
- **Archivos del proyecto:** Con `ADA_WORKSPACE` montado (en el compose actual: `.:/workspace`), si ADA escribe en su respuesta `READ_FILE: ruta/archivo` o `WRITE_FILE: ruta/archivo` + contenido + `END_FILE`, el sistema **ejecuta** esas operaciones en tu código. Es ejecución real en disco, no simulación.
- **Contexto persistente:** Memoria y ledger son servicios reales; lo que ADA “recuerda” o registra ahí queda guardado.

En ese sentido, **ADA puede trabajar como un Claude** para: hablar, leer/editar archivos del repo y usar memoria y finanzas reales.

---

## 3. Dónde hay simulación o límites

- **Simulación:** El motor de “simulación” (ROI, riesgo, etc.) existe para **evaluar** propuestas, no para fingir la conversación. La conversación y el LLM no son simulados.
- **Task-runner:** La llamada al task-runner es real, pero la implementación actual no envía emails reales, no publica en Gumroad, etc. Registra la tarea y devuelve éxito; los efectos en el mundo exterior son limitados hasta que se añadan integraciones.
- **Pasos “humano” del plan:** Cosas como “registrar en Gumroad” o “publicar oferta” no tienen automatización real todavía; ADA puede pedir ayuda (ej. Telegram) y un humano hace el paso o lo marca como hecho.

---

## 4. Conclusión

- **No es “todo simulación”:** La interacción con ADA usa un LLM real, archivos reales (READ_FILE/WRITE_FILE), memoria real y ledger real.
- **Sí puede trabajar como un Claude** en: conversación, edición de código del proyecto y uso de memoria y finanzas.
- **La “simulación”** está en la evaluación de propuestas (ROI/riesgo) y en que muchas acciones del mundo (compras, publicar ofertas, etc.) o no se ejecutan sin aprobación o no tienen aún integración real en task-runner.

Para acercar más ADA a “trabajar como Claude” en acciones externas, el paso siguiente es implementar en task-runner (o en agent-core) las integraciones reales que quieras (APIs de Gumroad, envío de correos, etc.) y seguir usando el mismo flujo de propuesta → política → ejecución.
