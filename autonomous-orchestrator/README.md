# A.D.A — Orquestador autónomo (Misión 6h)

Ejecuta la **Misión 6h**: aprendizaje completamente autónomo para generar un plan de ingresos digital, sin ejecutar task-runner hasta aprobación humana.

## Uso

Desde el host (con servicios en Docker):

```bash
cd autonomous-orchestrator
pip install -r requirements.txt
export AGENT_URL=http://localhost:3001
export MEMORY_URL=http://localhost:3005
export LOG_URL=http://localhost:3006
python orchestrator_6h.py
```

O dentro de la red Docker (por ejemplo desde un contenedor o mismo host con nombres de servicio):

```bash
export AGENT_URL=http://agent-core:3001
export MEMORY_URL=http://memory-db:3005
export LOG_URL=http://logging-system:3006
python orchestrator_6h.py
```

## Variables de entorno

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `AGENT_URL` | URL de agent-core | `http://agent-core:3001` |
| `MEMORY_URL` | URL de memory-db | `http://memory-db:3005` |
| `LOG_URL` | URL de logging-system | `http://logging-system:3006` |
| `MISSION_DURATION_HOURS` | Duración total en horas | `6` |
| `CYCLE_MINUTES` | Minutos entre ciclos (1 propuesta por ciclo) | `20` |
| `NOTIFY_INTERVAL_HOURS` | Intervalo de notificación (progress) | `2` |
| `TELEGRAM_BOT_TOKEN` | Token del bot Telegram (opcional) | — |
| `TELEGRAM_CHAT_ID` | Chat ID para enviar progreso (opcional) | — |

## Comportamiento

1. Inicializa contexto en memory-db (`ada_mission_context`, `ada_resources`, `ada_channels`).
2. Durante 6 h, cada `CYCLE_MINUTES`: envía una propuesta de ingreso digital a agent-core con **execute=false** (solo simulación + policy, sin task-runner).
3. Acumula resultados en `ada_proposals_6h` y actualiza `evolution_score`.
4. Cada `NOTIFY_INTERVAL_HOURS` escribe `ada_progress` en memory-db y logging, y opcionalmente envía un mensaje por Telegram.
5. Al finalizar, genera el plan final y lo guarda en **`final_plan_6h`** (pendiente de aprobación humana).

El progreso y el plan final se muestran en **Web-Admin** (sección "Misión 6h — Progreso y plan final").
