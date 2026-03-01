# A.D.A — MVP Interfaz Web y Chat Remoto

Interfaz local (Web-Admin con dashboard + chat) y chat remoto vía Telegram. Misma API (agent-core), flujo obligatorio respetado y Nivel 1 de autonomía.

---

## 1. Estructura del proyecto

```
ADA/
├── agent-core/           # API: /propose?execute=false, /execute_approved, /chat
├── logging-system/       # GET /events para dashboard
├── web-admin/
│   ├── src/
│   │   └── web_admin_api.py   # Backend FastAPI (proxy + /api/chat, /api/approve, /api/events, /api/score)
│   └── frontend/              # React (Vite)
│       ├── src/
│       │   ├── App.jsx       # Dashboard + chat + botones Aprobar/Rechazar/Re-simular
│       │   └── main.jsx
│       └── package.json
├── chat-bridge/          # Bot puente Telegram
│   └── src/
│       └── telegram_bot.py
└── docker-compose.yml   # web-admin + chat-bridge (perfil telegram)
```

---

## 2. Flujo respetado

- **Chat (web o Telegram):** mensaje → agent-core `/chat` → simulación → policy → logging (blocking ack) → **no ejecuta** (Nivel 1).
- **Aprobación humana:** usuario pulsa "Aprobar" → agent-core `/execute_approved` → log `human_approved` → task-runner.
- **Rechazo:** log `human_rejected` en logging-system.
- **Re-simular:** agent-core `/propose` con `execute=false` de nuevo.

Nunca se salta simulación, policy ni logging; nunca se ejecuta sin aprobación humana en Nivel 1.

---

## 3. Web-Admin local

### Backend (ya en Docker)

Con el stack levantado (`docker compose up -d`), el backend está en **http://localhost:8080**:

- `GET /api/score` — score evolutivo (memory-db, key `evolution_score`)
- `GET /api/events?limit=50` — últimos eventos (logging-system)
- `POST /api/chat` — envía mensaje a A.D.A (agent-core `/chat`)
- `POST /api/approve` — aprobación humana (agent-core `/execute_approved`)
- `POST /api/reject` — rechazo (registra en logging)
- `POST /api/resimulate` — re-simular propuesta

### Frontend React (desarrollo local)

```bash
cd web-admin/frontend
npm install
npm run dev
```

Se abre **http://localhost:5173** con proxy a `/api` y `/health` hacia el backend (configurar en `vite.config.js` el target si el backend no está en 8080).

### Frontend en producción (opcional)

```bash
cd web-admin/frontend
npm run build
```

Copiar la carpeta `dist` a `web-admin/frontend/dist`. Si el backend (u otro servidor) sirve estáticos desde `web-admin/frontend/dist`, la ruta `/` devolverá el React; si no existe `dist`, el backend sirve el dashboard HTML mínimo.

---

## 4. Chat remoto (Telegram)

### Crear el bot en Telegram

1. Abre [@BotFather](https://t.me/BotFather) en Telegram.
2. `/newbot` y sigue los pasos; copia el **token**.
3. Crea un `.env` en la raíz de ADA (o exporta):
   ```bash
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   ```

### Levantar el bot con Docker

```bash
docker compose --profile telegram up -d chat-bridge
```

O sin perfil, añadiendo el servicio y la variable:

```bash
export TELEGRAM_BOT_TOKEN=tu_token
docker compose up -d chat-bridge
```

El bot escucha mensajes; al escribir algo, llama a agent-core `/chat`, muestra la propuesta y botones **Aprobar ejecución**, **Rechazar**, **Re-simular**. Las interacciones quedan registradas en logging-system (y en PostgreSQL vía ada_logs).

### Conectar con Signal o Slack

El mismo flujo se puede replicar con:

- **Signal:** bot vía [signal-cli](https://github.com/AsamK/signal-cli) o un gateway Signal→HTTP; el gateway recibe el mensaje, llama a `AGENT_URL/chat` y devuelve la respuesta + acciones (enlace de aprobación, etc.).
- **Slack:** app Slack con Bot Token; servidor HTTP que recibe eventos de Slack y llama a agent-core; respuestas con bloques con botones (approve/reject) que llaman a `/execute_approved` o `/reject`.

La API compartida es siempre **agent-core** (y web-admin como proxy opcional).

---

## 5. Integración y consistencia

- **Misma API:** Web-Admin y Telegram (y cualquier otro cliente) usan agent-core: `/chat`, `/propose`, `/execute_approved`.
- **PostgreSQL:** logging-system escribe en `ada_logs.events`; el score puede leerse/escribirse en memory-db (`evolution_score`).
- **Score evolutivo:** se puede calcular en un job o en el backend y guardar en memory-db; el dashboard lo muestra con `GET /api/score`.

---

## 6. Resumen de comandos

| Acción | Comando |
|--------|--------|
| Levantar stack (sin Telegram) | `docker compose up -d` |
| Levantar con bot Telegram | `TELEGRAM_BOT_TOKEN=xxx docker compose --profile telegram up -d` |
| Frontend React en dev | `cd web-admin/frontend && npm install && npm run dev` |
| Backend + API | http://localhost:8080 (tras `docker compose up`) |
| Documentación API | http://localhost:8080/docs (FastAPI Swagger) |

Restricciones respetadas: no saltar simulación ni policy; no ejecutar sin logging ack; Nivel 1 = solo ejecutar con aprobación humana; no modificar constitución sin autorización.
