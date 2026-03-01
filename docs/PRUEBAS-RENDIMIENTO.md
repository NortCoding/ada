# Pruebas de rendimiento — A.D.A

## Versión probada: 0.2.0

**Fecha:** 2026-02-28  
**Cambio importante:** Prioridad cerebro externo (DeepSeek) para respuestas rápidas; historial reducido (4 msg); Ollama con num_ctx 2048, num_predict 512.

### Resultados

| Prueba | Configuración | Tiempo (ms) | Cerebro usado | Notas |
|--------|----------------|-------------|---------------|--------|
| Mensaje corto ("¿estás operativa?") | Default (API primero) | Timeout 120s | — | API no respondió en 45s; fallback a Ollama; curl cortó a 120s. |
| "Di solo: OK" | use_advanced_brain: false (solo Ollama) | 48 969 | ollama | Primera respuesta Ollama (modelo en frío). |
| "Responde en una sola palabra: listo" | Default (API primero) | 22 789 | ollama | API falló/timeout → Ollama; modelo ya caliente. |

### Conclusión

- **Versión 0.2.0** desplegada correctamente (GET /health, OpenAPI version).
- Flujo **API primero → Ollama fallback** operativo; cuando la API no responde, Ollama contesta.
- Con **solo Ollama** y contexto reducido: ~23–49 s según si el modelo está caliente o no.
- Si la API de DeepSeek responde, se esperan respuestas en **5–15 s**; comprobar `ADVANCED_BRAIN_API_KEY` y conectividad si se desea priorizar velocidad vía API.

---

## Cómo versionar

En cada **cambio importante** (nuevas capacidades, cambio de flujo de chat, resiliencia, rendimiento):

1. Actualizar `version` en `agent-core/src/agent_core_api.py` (FastAPI):
   - **0.x.0** → cambio relevante de comportamiento o arquitectura.
   - **0.1.x** → parches o ajustes menores en la misma línea.
2. Reconstruir y levantar: `docker compose build agent-core && docker compose up -d agent-core`.
3. Anotar en este documento la versión, fecha y resumen del cambio; opcional: añadir una fila en la tabla de resultados si se hacen pruebas.
