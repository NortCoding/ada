# Cómo está construida ADA y cómo funciona

Documento de referencia: arquitectura actual y flujos principales.

---

## 1. Vista general

**ADA (Agente Digital Autónomo)** es un agente que actúa como socio: tiene un plan de ingresos, memoria, chat (Ollama/Gemini) y ejecuta pasos de forma autónoma o pide ayuda cuando un paso es «humano» (ej. registrar en Gumroad). La interfaz humana es la **Web-Admin** (navegador) y opcionalmente **Telegram** (chat-bridge).

- **Cerebro:** Ollama en el host (modelo local, p. ej. llama3.2) y opcionalmente Google Gemini (API) para respuestas más avanzadas.
- **Persistencia:** PostgreSQL (esquemas `ada_memory`, `ada_finance`, `ada_logs`, etc.) y servicios que exponen API (memory-db, financial-ledger, logging-system).
- **Orquestación:** **agent-core** es el núcleo: recibe chat, consulta memoria y ledger, llama a Ollama/Gemini, y para tareas (propuestas) puede usar simulation-engine → policy-engine → task-runner.

---

## 2. Servicios (Docker Compose)

| Servicio | Puerto | Perfil | Función |
|----------|--------|--------|---------|
| **postgres** | 5432 | — | Base de datos central (todos los schemas). |
| **agent-core** | 3001 | — | Núcleo: chat con LLM, plan autónomo, execute_step, aprobaciones, notificación Telegram. |
| **memory-db** | 3005 | extended | API sobre `ada_memory.context`: planes (first_plan, weekly_plan), oferta, pasos, human_decisions, etc. |
| **financial-ledger** | 3004 | extended | API sobre `ada_finance`: balance, ingresos, transacciones. |
| **logging-system** | 3006 | extended | Registro de eventos (auditoría). |
| **simulation-engine** | 3007 | extended | Simula ROI, riesgo, impacto antes de aprobar una tarea. |
| **policy-engine** | 3008 | extended | Reglas de aprobación (¿se puede ejecutar esta propuesta?). |
| **task-runner** | 3003 | extended | Ejecución real de tareas aprobadas. |
| **web-admin** | 8080 | extended | Backend (FastAPI) + frontend (React): chat, plan y avances, seguimiento, finanzas, consola cerebro. |
| **chat-bridge** | 8081 | telegram | Bot de Telegram: mensajes → agent-core `/chat` (Ollama) y responde; envía notificaciones cuando ADA pide ayuda. |
| **n8n** | 5678 | extended | Automatizaciones (opcional). |

**Perfiles:**

- **Por defecto** (`docker compose up -d`): solo **postgres** y **agent-core**. Para uso real hace falta al menos memory-db (y normalmente el resto).
- **Extended** (`docker compose --profile extended up -d`): postgres + agent-core + memory-db + financial-ledger + logging-system + simulation-engine + policy-engine + task-runner + web-admin + n8n.
- **Telegram** (`docker compose --profile telegram up -d chat-bridge`): añade el bot de Telegram (depende de agent-core y logging).

Uso típico: `docker compose --profile extended --profile telegram up -d`.

**Ollama** no va en Docker en el setup actual: corre en el host (Mac). agent-core lo llama por `OLLAMA_URL` (p. ej. `http://host.docker.internal:11434`).

---

## 3. Estructura de carpetas (código)

```
ADA/
├── docker-compose.yml          # Servicios y perfiles
├── .env                         # Variables (no subir a repo)
├── ada_resources.env            # Recursos (Gemini, etc.)
├── infra/postgres/schemas/      # Schemas SQL (ada_memory, ada_finance, ada_logs…)
│
├── agent-core/                  # Núcleo (FastAPI)
│   ├── Dockerfile
│   └── src/agent_core_api.py    # Chat, plan, execute_step, approve, clear_plan, reset_all…
│
├── memory-db/                   # API memoria (FastAPI + PostgreSQL)
│   └── src/memory_api.py        # GET/SET por key, get_many, keys, export
│
├── financial-ledger/            # API finanzas (FastAPI + PostgreSQL)
├── logging-system/              # API logs
├── simulation-engine/          # Simulación de propuestas
├── policy-engine/               # Aprobación según reglas
├── task-runner/                 # Ejecución de tareas
│
├── web-admin/                   # Interfaz humana
│   ├── Dockerfile
│   ├── src/web_admin_api.py     # Proxy a agent-core, memory, ledger, chat, autonomous…
│   └── frontend/                # React (Vite): chat, pestañas Seguimiento / Panel / Plan / Consola / Finanzas
│
├── chat-bridge/                 # Bot Telegram
│   └── src/telegram_bot.py      # Mensajes → /chat, aprobar/rechazar, POST /send para notificaciones
│
├── signup-helper/               # Asistente registro (Gumroad, etc.) con Playwright
└── docs/                        # Documentación (este archivo, AUTONOMIA-ADA, INICIO-DESDE-CERO…)
```

---

## 4. Cómo funciona el chat

1. **Usuario** escribe en Web-Admin o envía un mensaje al bot de Telegram.
2. **Web-Admin** o **chat-bridge** llama a `POST /chat` de agent-core con `message` y opcionalmente `history`, `use_ollama`, `use_advanced_brain`.
3. **agent-core**:
   - Obtiene en paralelo: **memoria** (memory-db: first_plan, weekly_plan, requested_hardware_resources) y **balance** (financial-ledger). Usa una **caché en memoria** (TTL configurable, ej. 20 s) para no llamar a memory-db/ledger en cada mensaje cuando el contexto no ha cambiado.
   - Construye el **system prompt** (ADA_SYSTEM_PROMPT + contexto de finanzas, fecha, plan, correo de ADA, etc.).
   - Arma la lista de mensajes (system + últimos 4 del historial + mensaje actual).
   - Si `use_advanced_brain` y hay API key de Gemini: llama a **Gemini**; si no, usa **Ollama** (`/api/chat` o `/api/generate`).
   - Opcionalmente el mensaje puede llevar una **imagen** (`image_base64`): agent-core la envía a Ollama o Gemini para que ADA pueda describirla o responder sobre ella (modelos con visión: ej. `llava`, `llama3.2-vision` en Ollama).
   - Si está definido `ADA_WORKSPACE`, el prompt incluye instrucciones para usar **READ_FILE** y **WRITE_FILE**: la respuesta de Ollama puede contener líneas `READ_FILE: ruta/archivo` o `WRITE_FILE: ruta` + contenido + `END_FILE`; agent-core ejecuta esas acciones sobre el proyecto (montado en `/workspace`) e inyecta el resultado en la conversación para otra ronda.
   - Devuelve la respuesta; si hubo una **propuesta de tarea** (compra u otra) y la política no la auto-aprueba, devuelve `pending_approval` y en Web-Admin/Telegram el usuario puede Aprobar / Rechazar.
4. La respuesta se muestra en el chat; las decisiones (aprobar/rechazar) se registran en memory-db y opcionalmente en logging.

**Resumen:** Chat = agent-core + Ollama (o Gemini) + memoria + ledger; sin decision-engine por separado: la orquestación de propuestas (simular → policy → task) está dentro de agent-core.

---

## 5. Cómo funciona el plan autónomo

- **Plan:** Se guarda en memory-db en las claves `first_plan` y `weekly_plan` (objetivo, nicho, pasos con `action` y `tool`: Ollama, n8n, script, memoria, humano).
- **Crear plan:** `POST /autonomous/first_plan` → agent-core pide a Ollama un JSON de plan → lo guarda en memory-db y lo devuelve.
- **Consultar plan:** `GET /autonomous/plan` → agent-core lee first_plan/weekly_plan y estado de cada paso (plan_step_0_done, plan_step_0_result, etc.) y devuelve un único objeto `plan` para la UI.
- **Ejecutar un paso:** `POST /autonomous/execute_step?step_index=N` → agent-core toma el paso N del plan; si `tool` es "humano", no lo ejecuta, marca needs_help y puede notificar por Telegram (chat-bridge `/send`); si es Ollama/script/etc., puede ejecutarlo (p. ej. vía task-runner o lógica interna).
- **Marcar paso como hecho por humano:** `POST /autonomous/step_done?step_index=N&result=...` → actualiza plan_step_N_done y plan_step_N_result en memoria.
- **Siguiente paso pendiente:** `POST /autonomous/advance_next_step` → devuelve el índice del siguiente paso pendiente (para que un cron u orquestador llame a `execute_step`).
- **Limpiar plan:** `POST /autonomous/clear_plan` → borra first_plan, weekly_plan y estados de pasos en memory-db (value `null`). **Limpiar todo:** `POST /autonomous/reset_all?clear_chat=true|false` → además puede borrar oferta y historial de chat.

La **Web-Admin** muestra el plan en la pestaña «Plan y avances» / «Seguimiento»: resumen X de Y pasos, lista de pasos (Hecho / En curso / Pendiente), botón «Marcar como realizado» y botones «Solo plan» / «Limpiar todo e iniciar de nuevo».

---

## 6. Flujo de una propuesta (tarea)

Cuando el LLM (Ollama/Gemini) devuelve una **propuesta** que agent-core interpreta como tarea:

1. **agent-core** opcionalmente llama a **simulation-engine** (simular impacto).
2. **agent-core** llama a **policy-engine** (¿aprobado según reglas?). Si la propuesta es de tipo «compra» y no hay `simulated_approval` ni `ADA_AUTONOMOUS_PURCHASES=true`, se devuelve `pending_approval` y no se ejecuta hasta que el humano apruebe.
3. Si está aprobada: **agent-core** puede registrar en **logging-system** y enviar la tarea a **task-runner** para ejecución real.
4. El resultado vuelve a agent-core y se devuelve en la respuesta del chat o en el endpoint correspondiente.

Todo esto ocurre dentro de agent-core; no hay un servicio «decision-engine» separado en el compose actual.

---

## 7. Telegram

- **Chat con ADA:** El usuario escribe al bot → chat-bridge hace `POST /chat` a agent-core con `use_ollama: true` → muestra la respuesta de ADA; si hay `pending_approval`, muestra botones Aprobar/Rechazar.
- **Notificaciones cuando ADA pide ayuda:** Cuando un paso del plan es «humano», agent-core puede llamar a `CHAT_BRIDGE_URL/send` (con `TELEGRAM_CHAT_ID`) para enviar un mensaje al equipo (p. ej. «Necesito que registres la cuenta en Gumroad»).
- **Envío externo:** Cualquier servicio puede enviar mensajes a Telegram llamando a `POST http://chat-bridge:8081/send` con `text` y opcionalmente `chat_id`.

Variables necesarias: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (y en agent-core `CHAT_BRIDGE_URL`, `TELEGRAM_CHAT_ID` para notificaciones).

---

## 8. Resumen rápido

| Qué | Dónde |
|-----|--------|
| Cerebro (respuestas de texto) | Ollama en host + opcional Gemini en agent-core |
| Memoria (plan, oferta, pasos, decisiones) | memory-db → PostgreSQL `ada_memory` |
| Dinero (balance, ingresos) | financial-ledger → PostgreSQL `ada_finance` |
| Orquestación (chat, plan, ejecutar paso, aprobar) | agent-core (FastAPI, puerto 3001) |
| Interfaz humana | web-admin (puerto 8080) + opcional chat-bridge (Telegram, 8081) |
| Ejecución de tareas aprobadas | task-runner (con simulation-engine y policy-engine en modo extended) |
| Lectura/escritura de archivos del proyecto | agent-core `GET /autonomous/read_file`, `POST /autonomous/write_file` (cuando `ADA_WORKSPACE` está montado, ej. `.:/workspace`) |
| Caché de contexto de chat | agent-core (memoria + balance en RAM con TTL; variable `ADA_MEMORY_CACHE_TTL_SEC`) |

ADA está construida como un **conjunto de servicios en Docker** con **agent-core** como núcleo que usa **Ollama (y opcionalmente Gemini)** para el razonamiento y **memory-db** (y financial-ledger) para el estado persistente; la autonomía se controla con políticas y con pasos marcados como «humano» cuando no hay automatización (p. ej. Gumroad/Ko-fi). Ver también `docs/AUTONOMIA-ADA.md`, `docs/INICIO-DESDE-CERO.md` y `docs/MEJORAS-MEMORIA.md`.

