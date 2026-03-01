# Pruebas de funcionamiento (agent-core)

## Cómo ejecutar

Con agent-core en marcha (p. ej. `docker compose up -d`):

```bash
./scripts/run_agent_core_tests.sh
```

O con más tiempo para el chat (p. ej. 90 s):

```bash
CHAT_TIMEOUT=90 ./scripts/run_agent_core_tests.sh
```

Pruebas opcionales con Python (requiere `requests`):

```bash
cd agent-core && python3 tests/test_functional.py
# o con pytest:
cd agent-core && python3 -m pytest tests/test_functional.py -v -s
```

## Qué se prueba

| Prueba | Descripción |
|--------|-------------|
| **GET /health** | Que agent-core responde y devuelve `{"status":"ok","service":"agent-core"}`. |
| **POST /chat (Gemini)** | Con `use_advanced_brain: true`. Si `GEMINI_API_KEY` está configurada, se usa Google Gemini; si la API devuelve 429 (cuota agotada) o timeout, se hace fallback a Ollama. |
| **POST /chat (Ollama)** | Con `use_advanced_brain: false`. Respuesta desde Ollama local. Puede tardar según carga del modelo. |

## Notas

- **Modelo Gemini:** Por defecto se usa `gemini-2.0-flash` (la API ya no expone `gemini-1.5-flash` en el tier gratuito). Configurable con `GEMINI_MODEL`.
- **429 Quota exceeded:** En el plan gratuito de Gemini hay límite de uso. Si aparece 429, el chat hará fallback a Ollama. Puedes revisar uso en [Google AI Studio](https://aistudio.google.com/).
- **Timeout del chat:** Antes de llamar a Gemini u Ollama, agent-core consulta financial-ledger y memory-db. Si alguno tarda o no está en la red, el tiempo total puede ser alto; aumentar `CHAT_TIMEOUT` si es necesario.
