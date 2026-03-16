# Agentes especializados en ADA

Documento de diseño: cómo ADA puede tener agentes (o “voces”) especializados por tema.

> **Visión CEO:** Si quieres que **ADA sea el CEO** y tenga **agentes que ayuden a resolver problemas**, ver [ADA-COMO-CEO.md](ADA-COMO-CEO.md).

---

## 1. ¿Puede ADA tener agentes especializados?

**Sí.** Hoy ADA es un solo agente (agent-core) con un único prompt de sistema. Se puede extender de varias formas para que haya **especialistas por tema** (finanzas, código, marketing, visión, etc.) sin cambiar la arquitectura de servicios.

---

## 2. Enfoques posibles

### A) Especialistas por prompt (dentro de agent-core)

- **Idea:** Un solo servicio (agent-core), mismo Ollama/Gemini, pero **varios prompts de sistema** según el “rol” o tema.
- **Flujo:** El chat recibe un parámetro opcional (ej. `specialist: "finance"` o `specialist: "code"`). agent-core elige el prompt correspondiente y llama al LLM con ese sistema + historial.
- **Ventajas:** Fácil de implementar, sin nuevos contenedores. Cada especialista es un texto de sistema distinto (finanzas, código, marketing, etc.).
- **Uso:** En Web-Admin o Telegram el usuario elige “Hablar con ADA · Finanzas” o “ADA · Código”; el frontend envía ese `specialist` en el body del `/chat`.

### B) Subagentes como servicios

- **Idea:** Servicios separados (ej. `agent-finance`, `agent-code`) que exponen su propio `/chat` o `/ask`. agent-core hace de **orquestador**: según la intención o el tema, reenvía la pregunta al subagente y devuelve su respuesta (o la integra en una respuesta de ADA).
- **Ventajas:** Cada especialista puede tener su propio modelo, tiempo de respuesta y contexto. Mejor aislamiento.
- **Inconvenientes:** Más despliegue (más contenedores o procesos) y más latencia (llamadas entre servicios).

### C) Híbrido (recomendado para empezar)

- **Fase 1:** Especialistas por prompt (A) en agent-core: un diccionario `SPECIALIST_PROMPTS = {"finance": "...", "code": "...", "default": ADA_SYSTEM_PROMPT}` y en `POST /chat` un query/body `specialist` que selecciona el prompt.
- **Fase 2:** Si un tema crece mucho (ej. “código”), se puede extraer a un microservicio (B) más adelante.

---

## 3. Cambios mínimos para soportar especialistas (enfoque A)

1. **agent-core**
   - Definir `SPECIALIST_PROMPTS`: claves por tema (ej. `finance`, `code`, `marketing`) con el texto de sistema de cada uno. Incluir una clave `default` con el `ADA_SYSTEM_PROMPT` actual.
   - En el handler de `POST /chat` (o el que construye mensajes para Ollama/Gemini): leer `specialist` del body; si viene y existe en el diccionario, usar ese prompt como sistema; si no, usar `default`.
   - Opcional: que el historial se mantenga por `specialist` (ej. en memoria o en el cliente) para no mezclar temas.

2. **web-admin**
   - En el body de la petición de chat, añadir un campo opcional `specialist` (ej. valor del desplegable “ADA · Finanzas”, “ADA · Código”, “ADA (general)”).
   - Backend (web_admin_api) reenvía ese campo a agent-core en el proxy de `/chat`.

3. **Telegram (chat-bridge)**
   - Opcional: comando o botones para elegir especialista (ej. `/chat_finance`, `/chat_code`) y enviar `specialist` en el body a agent-core.

Con esto, ADA puede “tener” agentes especializados por tema usando el mismo núcleo y el mismo LLM, solo cambiando el prompt de sistema según el rol elegido.

---

## 4. Ejemplo de prompts por especialista

- **default:** El `ADA_SYSTEM_PROMPT` actual (socio general, supervivencia, plan de ingresos).
- **finance:** Enfocado en balance, ledger, ingresos/gastos, interpretar números y sugerir prioridades de gasto o de ingresos.
- **code:** Enfocado en READ_FILE/WRITE_FILE, sugerir cambios en el código del proyecto, scripts, integraciones; mencionar Antigravity IDE.
- **marketing:** Enfocado en ofertas, Gumroad/Ko-fi, tráfico, mensajes de venta, copy.

Cada uno puede reutilizar las mismas herramientas (memory-db, ledger, task-runner) pero con instrucciones y tono distintos en el prompt.

---

## 5. Resumen

| Pregunta | Respuesta |
|----------|-----------|
| ¿ADA puede tener agentes especializados? | Sí. |
| Enfoque más simple | Varios prompts de sistema en agent-core y un parámetro `specialist` en el chat. |
| Próximo paso | Añadir en agent-core el diccionario de prompts y la lógica en `/chat`; en web-admin el selector de especialista y el campo en la petición. |

Si quieres que se implemente el enfoque A (especialistas por prompt), se puede hacer en agent-core + web-admin en pocos pasos concretos.
