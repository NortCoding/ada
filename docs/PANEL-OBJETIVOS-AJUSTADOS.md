# Panel de agente — Objetivos ajustados al sistema actual

Los objetivos del panel se han adaptado al stack **existente** de ADA (Python/FastAPI + React + PostgreSQL) sin introducir Node.js ni SQLite. La persistencia y los logs históricos ya existen en **logging-system** y **memory-db**.

---

## Objetivo

Panel que permita visualizar en tiempo real:

1. Estado actual del agente  
2. Plan global  
3. Paso en ejecución  
4. Logs internos  
5. Decisiones tomadas  
6. Próximas acciones  

---

## Requisitos técnicos (ajustados)

| Requisito original | Ajuste en ADA |
|--------------------|----------------|
| Backend Node.js | **Backend Python** (web-admin FastAPI + agent-core). No se añade Node.js. |
| Base de datos simple (SQLite/JSON) | **PostgreSQL** ya en uso: `ada_logs.events` (logs), `ada_memory.context` (plan, estado, credenciales). |
| API local para estado del agente | **API en web-admin**: `/api/agent/status`, `/api/agent/complete-step`, `/api/agent/credentials`; agent-core ya expone plan, health, capabilities, step_done. |
| Frontend minimalista (React o HTML) | **React** ya en uso en web-admin; se añade pestaña **Panel** con las 4 secciones. |

---

## Arquitectura de endpoints

| Endpoint | Método | Uso |
|----------|--------|-----|
| `/api/agent/status` | GET | Estado agregado: objetivo global, estado, progreso %, plan, paso en ejecución, próximas acciones. |
| `/api/agent/update` | POST | (Opcional) Actualización de estado enviada por el agente; por ahora el estado se deriva de plan + logs. |
| `/api/agent/complete-step` | POST | Marcar paso como completado (proxy a `/api/autonomous/step_done`). |
| `/api/agent/credentials` | GET / POST | Indicar “credenciales proporcionadas” para una plataforma; metadata en memory-db (secretos en .env). |
| `/api/agent/plan-history` | GET | Listar planes anteriores a partir de eventos (autonomous_plan_created, plan_cleared). |

**Persistencia:**  
- Logs históricos: ya en `ada_logs.events`.  
- Plan actual y estado de pasos: en memory-db (`first_plan`, `weekly_plan`, `plan_step_*_done`).  
- Planes anteriores: derivados de eventos con `event_type` y `payload` correspondientes.

---

## Secciones del panel (frontend)

### SECCIÓN 1: Estado general
- Objetivo global (del plan en memoria).  
- Estado actual (modo producción, cerebro alcanzable, etc.).  
- Progreso % (pasos hechos / total pasos).

### SECCIÓN 2: Plan detallado
- Lista de pasos con estado: **pendiente** / **ejecutando** (si hay evento reciente `plan_step_started` para ese paso) / **terminado**.  
- Botón **“Marcar como completado”** en pasos que requieren humano.  
- Botón **“Proveer credenciales”** (enlace a formulario o modal que llama a `/api/agent/credentials` y luego completa el paso).

### SECCIÓN 3: Logs internos
- Qué está pensando (eventos tipo `thinking_*` o mensajes de cerebro).  
- Qué está buscando / qué decisiones tomó (eventos `proposal_generated`, `learning_recorded`, `plan_step_executed`, etc.).  
- Qué intentó ejecutar (`task_executed`, `plan_step_started`, `plan_step_needs_help`).  
- Fuente: `GET /api/events` (ya existente); filtros por `event_type` y `service_name`.

### SECCIÓN 4: Intervención humana
- Si el agente necesita registro o login: botón **“Ir a completar registro”** (URL de la plataforma desde `/api/autonomous/register_platforms`).  
- Tras completar: opción de marcar “credenciales proporcionadas” (POST `/api/agent/credentials`), marcar paso como resuelto (POST `/api/agent/complete-step`) y continuar.

---

## Estructura de carpetas (sin cambios)

El panel se integra en el proyecto actual:

```
web-admin/
  src/
    web_admin_api.py     # + rutas /api/agent/*
  frontend/
    src/
      App.jsx            # + pestaña Panel con 4 secciones
```

No se crean carpetas nuevas; solo se extienden backend y frontend existentes.

---

## Sistema de estados

- **Estado del agente** se deriva de:  
  - `GET /autonomous/plan` (plan + step_statuses),  
  - `GET /health` y `GET /autonomous/capabilities` (agent-core),  
  - Últimos eventos de logging (`plan_step_started`, `plan_step_executed`, `plan_step_completed`, `plan_step_needs_help`).  
- **Paso en ejecución:** si existe un evento reciente `plan_step_started` con `step_index = i`, el paso `i` se considera “ejecutando” hasta que aparezca `plan_step_executed` o `plan_step_needs_help` o `plan_step_completed`.

---

## Credenciales

- No se guardan contraseñas en memoria; las credenciales sensibles siguen en `.env` (ADA_EMAIL, ADA_EMAIL_PASSWORD, etc.).  
- En memory-db se puede guardar solo metadata por plataforma, por ejemplo: `credentials_gumroad = { configured: true, note: "Ver .env" }` para indicar que “el humano ya configuró credenciales” y permitir marcar el paso como resuelto.
