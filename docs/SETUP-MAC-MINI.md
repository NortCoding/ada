# A.D.A en Mac mini — Configuración recomendada

Configuración para ejecutar ADA en una **Mac mini** con Ollama instalado de forma **nativa** (sin contenedor Docker). El agent-core corre en Docker y se conecta a Ollama en el host mediante `host.docker.internal`.

---

## Requisitos

- **macOS** (Mac mini, Intel o Apple Silicon)
- **Docker Desktop** para Mac (incluye soporte de `host.docker.internal`)
- **Ollama** instalado en el sistema (no en Docker): [ollama.com](https://ollama.com) o `brew install ollama`

---

## 1. Ollama en el host (Mac mini)

1. **Instalar Ollama** (si no está):
   ```bash
   brew install ollama
   ```
   O descarga desde [ollama.com](https://ollama.com).

2. **Arrancar Ollama** (si no corre como servicio):
   ```bash
   ollama serve
   ```
   En muchas instalaciones Ollama ya corre en segundo plano. Comprueba:
   ```bash
   curl -s http://localhost:11434/api/tags
   ```
   Debe devolver JSON con los modelos (o `{"models":[]}` si aún no hay ninguno).

3. **Dejar el modelo listo para ADA** (local y gratuito). Desde la raíz del proyecto:
   ```bash
   ./scripts/setup_ollama_model.sh
   ```
   Ese script comprueba que Ollama esté en marcha y descarga el modelo por defecto (`llama3.2`). Si prefieres hacerlo a mano: `ollama pull llama3.2`. Opcional: en `ada_resources.env` puedes poner `OLLAMA_MODEL=otro-modelo` y ejecutar el script (o `ollama pull otro-modelo`).

---

## 2. Variables de entorno (opcional)

En la raíz del proyecto puedes tener un `.env` (no subido a git). Para Mac mini **no hace falta** definir `OLLAMA_URL`: el `docker-compose` ya usa por defecto:

- `OLLAMA_URL=http://host.docker.internal:11434/api/generate`

Eso permite que el contenedor `agent-core` alcance Ollama en tu Mac. Solo define `OLLAMA_URL` si Ollama está en otra máquina o puerto.

Opcional en `.env` o `ada_resources.env`:

- `OLLAMA_MODEL=llama3.2` (o el modelo que uses)
- `OLLAMA_CHAT_TIMEOUT=120` si las respuestas son muy largas

---

## 3. Levantar ADA (Docker)

Desde la raíz del proyecto:

```bash
docker compose up -d --build
```

Esto levanta **postgres** y **agent-core** (y con `--profile extended` el resto de servicios). **No** se levanta ningún contenedor de Ollama; agent-core usará Ollama en tu Mac vía `host.docker.internal`.

Comprobar que agent-core ve a Ollama:

```bash
curl -s http://localhost:3001/autonomous/ollama_status
```

Deberías ver `"reachable": true` y que el modelo configurado esté listo.

---

## 4. Resumen rápido (Mac mini)

| Paso | Comando / acción |
|------|-------------------|
| Ollama en marcha | `ollama serve` o abrir la app Ollama; `curl -s http://localhost:11434/api/tags` |
| Modelo listo | `./scripts/setup_ollama_model.sh` (o `ollama pull llama3.2`) |
| Levantar ADA | `docker compose up -d` |
| Comprobar cerebro | `curl -s http://localhost:3001/autonomous/ollama_status` o en web-admin → ConsolaCerebro |

En **Mac (Mac mini)** no hace falta configurar nada extra para `host.docker.internal`; Docker Desktop ya lo resuelve.
