# A.D.A — F0 a F5 (MVP operativo)

## Flujo (F5 completo)

```
[web-admin] → agent-core → simulate → policy → log → task-runner → log
                    │                                    │
                    ├→ memory-db (estado/score)          ├→ financial-ledger (transacciones)
                    └→ PostgreSQL (ada_logs, ada_finance, ada_memory)
```

## Requisitos

- Docker y Docker Compose
- **Ollama** en el host (nativo): para el chat, ADA usa Ollama instalado en la máquina, no en Docker. En **Mac mini / Mac** ver [docs/SETUP-MAC-MINI.md](docs/SETUP-MAC-MINI.md).
- (Opcional) Copiar `.env.example` a `.env` y cambiar `PG_PASSWORD`

## Levantar

```bash
docker compose up -d --build
```

PostgreSQL crea los schemas en el **primer** arranque (volumen vacío). Si ya tenías `pg-data` de antes, aplica los schemas que falten:

```bash
# Solo si falta ada_policies:
docker exec -i ada_postgres psql -U ada_user -d ada_main < infra/postgres/schemas/ada_policies.sql
# Solo si falta ada_finance.transactions:
docker exec -i ada_postgres psql -U ada_user -d ada_main < infra/postgres/schemas/ada_finance_ledger.sql
```

(O bien `docker compose down -v` y volver a levantar para BD limpia.)

## Primer ciclo de prueba (F0 + F2 + F3)

### 1. Simular propuesta (simulation-engine)

```bash
curl -X POST http://localhost:3007/simulate \
  -H "Content-Type: application/json" \
  -d '{"proposal": {"task": "test_mvp"}}'
```

Ejemplo de respuesta:

```json
{"ROI": 0.75, "risk": 0.22, "impact_financial": 5421.34, "infra_cost": 312.5}
```

### 2. Consultar política (policy-engine)

```bash
curl -X POST http://localhost:3008/approve \
  -H "Content-Type: application/json" \
  -d '{"service_name":"agent-core","action_type":"test_mvp","payload":{}}'
```

Respuesta esperada:

```json
{"approved": true, "reason": "Regla activa encontrada"}
```

### 3. Registrar evento (logging-system, blocking ack)

```bash
curl -X POST http://localhost:3006/log \
  -H "Content-Type: application/json" \
  -d '{"service_name":"agent-core","event_type":"proposal_test","payload":{"ROI":0.75,"risk":0.22}}'
```

Respuesta: `{"status":"ok","event_id":<id>}`.

### 4. Health de todos los servicios

```bash
curl -s http://localhost:3006/health  # logging
curl -s http://localhost:3007/health # simulation
curl -s http://localhost:3008/health # policy
```

### 5. Comprobar en PostgreSQL

```bash
docker exec -it ada_postgres psql -U ada_user -d ada_main -c "SELECT * FROM ada_logs.events;"
docker exec -it ada_postgres psql -U ada_user -d ada_main -c "SELECT * FROM ada_policies.rules;"
```

## Flujo F4: agent-core + task-runner

Una vez levantados todos los servicios (incl. Ollama opcional):

### Propuesta directa (sin LLM)

```bash
curl -X POST http://localhost:3001/propose \
  -H "Content-Type: application/json" \
  -d '{"task_name":"test_mvp","details":{"description":"Probar F4"}}'
```

Respuesta esperada (ejemplo):

```json
{
  "simulation": {"ROI": 0.73, "risk": 0.15, "impact_financial": 5210, "infra_cost": 300},
  "policy": {"approved": true, "reason": "Regla activa encontrada"},
  "task_result": {"status": "success", "details": {"description": "Probar F4"}}
}
```

### Generar propuesta con Ollama (opcional)

Requiere que el contenedor Ollama esté arriba y un modelo (ej. `ollama pull llama3.2`):

```bash
curl -X POST http://localhost:3001/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Propón una tarea de prueba con task_name y description."}'
```

### Health F4

```bash
curl -s http://localhost:3001/health  # agent-core
curl -s http://localhost:3003/health  # task-runner
```

## F5: financial-ledger + memory-db + web-admin

### Financial-ledger — transacción de prueba

```bash
curl -X POST http://localhost:3004/transaction \
  -H "Content-Type: application/json" \
  -d '{"type":"income","amount":1000,"description":"Test revenue"}'
```

### Memory-db — guardar y leer métricas (score evolutivo)

```bash
# Guardar
curl -X POST http://localhost:3005/set \
  -H "Content-Type: application/json" \
  -d '{"key":"proposal_001","value":{"ROI":0.8,"risk":0.1,"efficiency":0.9}}'

# Leer
curl -s http://localhost:3005/get/proposal_001
```

### Web-admin — dashboard

- **URL:** http://localhost:8080
- Desde el dashboard puedes: enviar propuestas (agent-core), guardar/leer memoria, crear transacciones y listar transacciones.

### Health F5

```bash
curl -s http://localhost:3004/health  # financial-ledger
curl -s http://localhost:3005/health # memory-db
curl -s http://localhost:8080/health # web-admin
```

## Bajar

```bash
docker compose down
```

Para borrar volúmenes: `docker compose down -v`.

---

**Resultado:** A.D.A MVP operativo: propuestas (agent-core), simulación, políticas, logging, task-runner, financial-ledger, memory-db y web-admin. Datos listos para calcular score evolutivo (ROI, riesgo, eficiencia, transacciones).
