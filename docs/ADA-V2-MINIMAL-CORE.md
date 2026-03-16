# ADA v2 Minimal Core

Arquitectura mínima y estable para el agente ADA: conversación, memoria, estrategia y bucle de pensamiento autónomo.

## Servicios por defecto

Al ejecutar `docker compose up -d` se levantan solo:

| Servicio        | Contenedor           | Puerto | Rol                                      |
|-----------------|----------------------|--------|------------------------------------------|
| postgres        | ada_postgres         | 5432   | Persistencia (schemas ada_memory, ada_core) |
| ada_core        | ada_core             | 3001   | Motor de IA, conversación, scheduler     |
| memory_service  | ada_memory_service   | 3005   | API de memoria key-value                 |
| chat_interface  | ada_chat_interface   | 8080   | Interfaz web para conversar con ADA      |

**Ollama** corre en el host (Mac Mini), no en Docker. Por defecto se usa `http://host.docker.internal:11434`.

### Si arrancan más servicios de la cuenta

Con `docker compose up -d` solo deben levantarse los 4 de la tabla. Si ves más (por ejemplo `ada_chat_bridge`):

1. **Variable de entorno:** Si tienes `COMPOSE_PROFILES` definida (p. ej. `telegram`), Docker Compose arranca también los servicios de ese perfil. Para solo los 4, no definas `COMPOSE_PROFILES` o déjala vacía en tu `.env`.
2. **Contenedores de una ejecución anterior:** Si antes usaste `docker compose --profile telegram up -d`, el chat-bridge puede seguir en ejecución. Para pararlo: `docker compose stop chat-bridge`.
3. **Comprobar qué está en marcha:** `docker compose ps` — deberías ver solo `ada_postgres`, `ada_core`, `ada_memory_service`, `ada_chat_interface` como "Up" si no usas perfiles.

## Perfil extended

Servicios opcionales (simulación, policy, ledger, task-runner, logging, n8n) se levantan con:

```bash
docker compose --profile extended up -d
```

No se eliminan; quedan bajo el perfil `extended` para uso futuro.

## Módulos internos (ada_core)

Dentro del servicio `ada_core` (build: `./agent-core`):

- **reasoning_engine**: Prompts estructurados vía Ollama; nunca lanza excepciones.
- **conversation_engine**: Procesa mensajes del usuario y genera respuestas con el prompt v2.
- **memory_manager**: KV vía memory_service (HTTP) y goals/memories/ideas vía Postgres (schema `ada_core`).
- **strategy_engine**: Analiza metas activas y genera ideas (para el scheduler).
- **scheduler**: Bucle en segundo plano; cada hora lee metas activas, genera ideas y las guarda.

## Base de datos (ADA v2)

Schema `ada_core` (creado por `infra/postgres/schemas/ada_core.sql`):

- **goals**: id, goal, status, created_at
- **memories**: id, timestamp, topic, content, importance
- **ideas**: id, goal_id, idea, score, created_at

## API v2 (ejemplos)

- `GET /v2/goals` — Lista metas activas (no falla; devuelve `[]` si no hay o hay error).
- `POST /v2/goals` — Añade una meta (body: `{"goal": "..."}`).
- `GET /v2/ideas?goal_id=1` — Ideas asociadas a una meta.
- `POST /v2/chat` — Conversación mínima (body: `{"message": "...", "history": [...]}`).

Respuestas seguras: si el servicio de memoria o Postgres no está disponible, se devuelven listas vacías o mensajes de fallback sin tumbar el proceso.

## Scheduler (pensamiento autónomo)

Cada hora (configurable con `ADA_SCHEDULER_INTERVAL_SEC`, default 3600):

1. Obtiene metas activas (`ada_core.goals` con `status = 'active'`).
2. Para cada meta, llama al LLM para generar ideas.
3. Guarda las ideas en `ada_core.ideas`.

El scheduler se arranca en un hilo daemon al levantar la API; si no hay metas, no hace nada.

## Prompt por defecto (ADA v2)

Se usa en el motor de conversación v2 y en el reasoning:

```
You are ADA, a strategic AI partner helping build and evolve this project.

Your responsibilities:
- analyze ideas
- question assumptions
- propose improvements
- think strategically
- help grow the system.

You are not just a chatbot.
You are part of the founding team.
```

## Ollama

- **Modelo por defecto**: `llama3:8b` (variable `OLLAMA_MODEL`).
- **Fallback**: `qwen2:7b` (variable `OLLAMA_FALLBACK_MODEL`).

Ambos configurables por entorno. Recomendado para Mac Mini M1 16GB: `llama3:8b` o `qwen2:7b`.

## Estabilidad

- El sistema no se cae si memory_service no responde: se usan valores por defecto o listas vacías.
- Si la tabla `goals` está vacía, el scheduler no hace nada y no lanza errores.
- Los endpoints v2 devuelven respuestas seguras (mensaje de cortesía o `[]`) cuando un servicio no está disponible.
