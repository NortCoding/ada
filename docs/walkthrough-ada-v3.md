# ADA v3 — Walkthrough

Resumen de la interfaz y la plataforma multi-agente ADA v3.

## Interfaz principal

- **Panel de chat (izquierda):** Conversación con ADA. Según el workspace activo, el agente usa solo las habilidades de ese tipo (developer, business, research, general).
- **Explorador de archivos y visor de código (centro):** Árbol de archivos (raíz = directorio asignado, p. ej. `/Volumes/Datos/dockers`) y visor de código con colores estilo Dracula.
- **Panel de previsualización y sistema (derecha):** Pestañas Vista Previa (proyecto), Avance (plan) y Sistema (estado del agente).

## Dashboard (entrada)

Al abrir la aplicación se muestra el **Dashboard** con botones:

| Workspace        | Descripción                                      |
|------------------|--------------------------------------------------|
| Developer Lab    | Desarrollo y análisis de código (coding, code_review, architecture). |
| Business Lab     | Ideas de negocio y oportunidades (strategy, research, opportunity_engine). |
| Research Lab     | Investigación y conocimiento (web_research, learning). |
| General          | Estrategia e investigación general.              |
| Agent Market     | Ver y proponer nuevos agentes (solo propuestas; requieren aprobación humana). |
| System Monitor   | Estado interno: metas, oportunidades, experiencias, planes. |

Al elegir un workspace de agente (Developer, Business, Research, General) se abre la vista de tres paneles; el chat envía `agent_type` para que ADA use solo las habilidades de ese agente.

## Módulos v3 (backend)

- **agent_manager:** Define `AGENTS` (developer, business, research, general) y sus habilidades; `get_agent_skills(agent_type)`, `list_agents()`.
- **conversation_engine:** Acepta `agent_type` en `respond()` y `respond_structured()`; carga solo las habilidades del agente seleccionado.
- **agent_market:** Propuestas de nuevos agentes en tabla `ada_core.agent_proposals`; `propose_new_agent()`, `list_agent_proposals()`; sin creación automática.
- **knowledge_base:** Tabla `ada_core.knowledge_base` (topic, source_url, summary); `MemoryManager.add_knowledge()`, `get_knowledge_by_topic()`.
- **respond_structured:** Respuestas con secciones Análisis, Propuesta, Riesgos, Siguiente paso (ya existente; compatible con agent_type).

## API relevante

- `POST /chat` — body con `message`, `history`, opcional `agent_type` (developer | business | research | general).
- `GET /v3/agents` — lista de tipos de agente.
- `GET /agent_market/proposals` — listado de propuestas.
- `POST /agent_market/propose` — proponer nuevo agente (domain, required_skills, purpose).
- `GET /system/monitor` — estado del sistema (metas, oportunidades, experiencias, planes).

## Compatibilidad

- Ollama local como LLM por defecto.
- PostgreSQL (schemas ada_core: goals, memories, ideas, experiences, opportunities, agent_proposals, knowledge_base).
- Módulos existentes: scheduler, research_engine, opportunity_engine, memory_manager. Los fallos en habilidades o herramientas devuelven respuestas de fallback seguras.
