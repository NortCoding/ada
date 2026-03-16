# Por qué falla el cerebro (chat) y cómo corregirlo

**Base:** ADA usa **Ollama como cerebro base** (gratis, local). Todo el chat pasa por Ollama por defecto. **Gemini** es de pago: solo se usa cuando el usuario lo pide explícitamente (`use_advanced_brain=true`) o cuando hace falta más capacidad (ej. análisis complejo). Prioridad: al máximo local y gratuito; Gemini solo si se necesita más. Si el chat no responde, suele ser porque Ollama no está en marcha o no es alcanzable.

---

## 1. Cómo funciona el flujo del chat

1. **Cerebro avanzado (Google Gemini)**  
   Se usa cuando en la petición se envía `use_advanced_brain=true` **y** está configurado `GEMINI_API_KEY` (API gratuita).  
   - Si responde bien → se devuelve esa respuesta.  
   - Si **falla o hace timeout (45 s)** → se pasa al cerebro base.

2. **Cerebro base (Ollama)**  
   Se llama a la URL configurada en `OLLAMA_URL` (por defecto en Mac: `http://host.docker.internal:11434`; en host directo: `http://localhost:11434`).  
   - Si Ollama **no está en marcha** o **no es alcanzable** → la petición hace timeout (120 s por defecto) y ves el mensaje “Ollama no responde”.

3. **Resumen**  
   - Timeout ~45 s y luego otro timeout → puede ser: **Gemini hace timeout** y luego **Ollama no responde**.  
   - Mensaje explícito “Ollama no responde” → **solo falla Ollama** (Gemini ya se saltó o no está configurado).

---

## 2. Cerebro avanzado (Google Gemini) – por qué falla y qué hacer

| Causa | Qué hacer |
|-------|-----------|
| **API key vacía o inválida** | En `ada_resources.env` (o env de `agent-core`): `GEMINI_API_KEY=AIza...`. Obtén una key gratuita en [Google AI Studio](https://aistudio.google.com/apikey). |
| **Timeout 45 s** | El modelo tarda mucho. Se hace fallback a Ollama. Para respuestas más largas puedes subir `timeout` en `_call_gemini`. |
| **Modelo incorrecto** | Por defecto: `GEMINI_MODEL=gemini-1.5-flash`. También válido: `gemini-1.5-pro`, `gemini-2.0-flash`. |
| **Error 4xx/5xx** | Revisa logs: `docker logs ada_core 2>&1`. Se imprime `GEMINI FAIL` o `GEMINI ERROR` con código y mensaje. |

**Comprobar que el avanzado no rompe todo:**  
Si quitas o vacías `GEMINI_API_KEY`, el chat **solo** usará Ollama (no se intentará Gemini).

---

## 3. Cerebro base (Ollama) – por qué falla y qué hacer

Ollama se usa **nativo en el host** (no hay contenedor Docker de Ollama). En **Mac (Mac mini)** agent-core en Docker se conecta al host con `OLLAMA_URL=http://host.docker.internal:11434/api/generate` por defecto.

| Causa | Qué hacer |
|-------|-----------|
| **Ollama no está en marcha en el host** | Inicia Ollama en la Mac: `ollama serve` o abre la app Ollama. Comprueba: `curl -s http://localhost:11434/api/tags`. Ver también [SETUP-MAC-MINI.md](SETUP-MAC-MINI.md). |
| **agent-core (Docker) no alcanza a Ollama** | En Mac/Windows el valor por defecto `OLLAMA_URL=http://host.docker.internal:11434/api/generate` suele bastar. Comprueba que Docker Desktop esté en marcha y que en el host `curl -s http://localhost:11434/api/tags` responda. Si Ollama está en otra máquina, define `OLLAMA_URL` en `.env` con la URL correcta. |
| **Modelo no descargado** | En el host: `./scripts/setup_ollama_model.sh` (desde la raíz del proyecto) o `ollama pull llama3.2`. Comprueba: `ollama list`. |
| **Timeout (120 s)** | Prompt/historial muy largo o máquina lenta. Sube `OLLAMA_CHAT_TIMEOUT` (ej. 180) en `ada_resources.env` o en `environment` de `agent-core`. |

**Comprobar Ollama en el host (Mac mini):**  
```bash
curl -s http://localhost:11434/api/tags    # desde la Mac
ollama list                                 # modelos instalados
```

**Comprobar que el contenedor ada_core alcanza a Ollama (Mac):**  
```bash
docker exec ada_core curl -s --connect-timeout 5 http://host.docker.internal:11434/api/tags
```  
Si esto falla (timeout o connection refused), Ollama no es alcanzable desde Docker. Asegúrate de que Ollama esté en marcha en la Mac y que `OLLAMA_URL` en docker-compose sea `http://host.docker.internal:11434/api/generate`.

---

## 4. ¿Falta algún microservicio?

**No.** Para el chat solo hacen falta los 4 servicios por defecto: **postgres**, **memory_service**, **ada_core**, **chat_interface**. El "cerebro" es **Ollama en el host** (no es un contenedor). Comprueba: `docker compose ps` — los cuatro deben estar "Up". Si falta alguno: `docker compose up -d`.

---

## 5. Checklist rápido

1. **¿Ollama está en marcha en el host (Mac)?**  
   `curl -s http://localhost:11434/api/tags` y/o `ollama list`. En web-admin, pestaña **ConsolaCerebro**, verás "Ollama: alcanzable" o "no alcanzable".

2. **¿El modelo está en Ollama?**  
   En la Mac: `ollama list`. Si falta: `ollama pull llama3.2` (o el de `OLLAMA_MODEL`).

3. **¿La API key del cerebro avanzado (Gemini) está puesta?**  
   En `ada_resources.env`: `GEMINI_API_KEY=...`. Si la dejas vacía, el chat solo usará Ollama.

4. **¿Qué dice agent-core en los logs?**  
   `docker logs ada_core 2>&1 | tail -50` — busca `ADV_BRAIN FAIL`, `OLLAMA CHAT FAIL`, `OLLAMA ERROR`.

5. **¿Quieres solo Ollama (sin avanzado) para probar?**  
   Quita o comenta `GEMINI_API_KEY` en el env de agent-core, reinicia agent-core y prueba el chat de nuevo.

---

## 6. Variables de entorno relevantes (agent-core)

| Variable | Uso |
|----------|-----|
| `OLLAMA_URL` | URL de Ollama. En Mac con Ollama en el host: por defecto `http://host.docker.internal:11434/api/generate`. Se deriva la URL de chat. |
| `OLLAMA_MODEL` | Modelo a usar (ej. `llama3.2`). |
| `OLLAMA_CHAT_TIMEOUT` | Timeout en segundos para /api/chat (default 180; la primera respuesta puede tardar si el modelo se carga). |
| `GEMINI_API_KEY` | Key de Google Gemini (cerebro avanzado). Si vacía, solo se usa Ollama. |
| `GEMINI_MODEL` | Modelo Gemini (ej. `gemini-2.0-flash`). |

Si tras esto el cerebro sigue fallando, el siguiente paso es revisar los logs de `ada_agent_core` en el momento exacto en que envías el mensaje al chat.
