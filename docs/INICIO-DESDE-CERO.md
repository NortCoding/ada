# Limpiar todo e iniciar de nuevo

Documentación para resetear el estado de ADA y volver a empezar sin errores.

---

## Qué se limpia

Al ejecutar **«Limpiar todo»** (endpoint `POST /autonomous/reset_all`):

| Qué | Dónde | Efecto |
|-----|--------|--------|
| Plan (first_plan, weekly_plan) | memory-db | Se borra el plan de ingresos. |
| Primera oferta (first_offer) | memory-db | Se borra la oferta creada por ADA. |
| Estados de pasos (plan_step_*_done, plan_step_*_result) | memory-db | Se borran los “hecho” y resultados de cada paso. |
| plan_steps_status | memory-db | Se vacía. |
| Chat (opcional) | memory-db | Si eliges `clear_chat=true`, se borra el historial de chat. |

**No se borra:** logs en PostgreSQL, balance en financial-ledger, decisiones humanas en memory-db (human_decisions), ni configuración (.env, Docker). Solo el estado operativo de ADA (plan, oferta, avances y opcionalmente chat).

---

## Cómo ejecutar «Limpiar todo»

### Opción 1: Web-Admin (recomendado)

1. Abre **Plan y avances**.
2. Usa el botón **«Limpiar todo e iniciar de nuevo»** (si está disponible).
3. Opcional: marca **«Incluir historial de chat»** si quieres borrar también el chat.
4. Confirma. Se llamará a `POST /api/autonomous/reset_all`.

### Opción 2: API (curl)

Solo plan, oferta y pasos (sin borrar chat):

```bash
curl -X POST http://localhost:8080/api/autonomous/reset_all
```

Incluir también el historial de chat:

```bash
curl -X POST "http://localhost:8080/api/autonomous/reset_all?clear_chat=true"
```

Si llamas directo a agent-core (puerto 3001):

```bash
curl -X POST http://localhost:3001/autonomous/reset_all
curl -X POST "http://localhost:3001/autonomous/reset_all?clear_chat=true"
```

### Opción 3: Solo plan (no oferta ni chat)

Si solo quieres borrar el plan y los pasos (mantener primera oferta y chat):

- Web-Admin: **«Limpiar y empezar de cero»** en Plan y avances (llama a `clear_plan`).
- O: `curl -X POST http://localhost:8080/api/autonomous/clear_plan`

---

## Después de limpiar: iniciar de nuevo

1. **Crear plan**
   - En Web-Admin, pestaña **Plan y avances** → **«Que ADA genere el plan ahora»**.
   - O en el chat: pide a ADA que proponga un plan.

2. **Seguimiento**
   - Pestaña **Seguimiento** para ver el plan paso a paso y el avance.

3. **Si quieres primera oferta de nuevo**
   - Pídelo en el chat («crea la oferta», «crear primera oferta») o usa el flujo de producción si está expuesto.

No hace falta reiniciar contenedores; con el reset basta para que ADA quede “en cero” a nivel de plan y oferta.

---

## Estado del proyecto (referencia sin errores)

- **Servicios:** postgres, agent-core, memory-db, financial-ledger, logging-system; opcionales: simulation-engine, policy-engine, task-runner, web-admin, n8n, chat-bridge (Telegram).
- **Flujo típico:** Plan (first_plan) → pasos (Ollama o humano) → primera oferta (first_offer) → registro/publicación humana o asistida.
- **Memoria (memory-db):** first_plan, weekly_plan, first_offer, plan_step_*_done/result, chat_history, requested_hardware_resources, human_decisions.
- **Docs relacionados:** `AUTONOMIA-ADA.md`, `PRODUCCION.md`, `SETUP-MAC-MINI.md`.

Si algo falla al limpiar o al iniciar de nuevo, revisa que agent-core y memory-db estén en marcha y que la URL de agent-core en web-admin sea la correcta.
