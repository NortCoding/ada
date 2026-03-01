# A.D.A — Arquitectura del Sistema v0.2 (Agente Digital Autónomo)

Documento de diseño técnico. Sin implementación ni código.  
**Versión 0.2:** gobernanza, simulación, PostgreSQL centralizado, logging con acknowledgement, stateless/stateful y plan de migración.

---

## 1. Arquitectura lógica actualizada (v0.2)

### 1.1 Diagrama de capas

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CAPA DE INTERACCIÓN HUMANA                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         web-admin (interfaz humano-agente)                 │  │
│  │  • Dashboard • Aprobaciones • Configuración • Visualización • Políticas   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                           │
│                          HTTP/WebSocket (único punto expuesto al host)           │
└──────────────────────────────────────┼───────────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CAPA DE ORQUESTACIÓN                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         agent-core (interacción con LLM)                   │  │
│  │  • Ollama • Intenciones • Propuestas • NO reglas • NO ejecución            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │ propuestas                                │
│                                      ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                      decision-engine (evaluación estratégica)              │  │
│  │  • Orquesta flujo • CERO reglas hardcodeadas • Consulta policy-engine     │  │
│  │  • Pide simulación → consulta política → aprueba/rechaza → task-runner    │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                    │                    │                      │                  │
│                    │ simular            │ ¿aprobado?            │ comando         │
│                    ▼                    ▼                      ▼                  │
│  ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐  │
│  │  simulation-engine   │   │  policy-engine       │   │  task-runner         │  │
│  │  • ROI estimado      │   │  • Todas las reglas  │   │  • Ejecución real    │  │
│  │  • Riesgo estimado   │   │  • Gobernanza        │   │  • Solo si aprobado  │  │
│  │  • Impacto financiero│   │  • Modificable sin   │   │  • Resultados        │  │
│  │  • Costo infra       │   │    tocar otros SVC   │   │                      │  │
│  └──────────────────────┘   └──────────────────────┘   └──────────────────────┘  │
└──────────────────────────────────────┼───────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌─────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
│  financial-      │         │  memory (API)       │         │  logging-system     │  │
│  ledger (API)    │         │  • Estado/contexto  │         │  • Blocking ack      │  │
│  • Registro      │         │  • Historial       │         │  • Si falla → abort  │  │
│    económico     │         │  • Schema ada_memory│         │  • Auditoría        │  │
└─────────────────┘         └─────────────────────┘         └─────────────────────┘  │
         │                             │                             │
         └─────────────────────────────┼─────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL CENTRALIZADO (un solo servidor)                     │
│  Schemas: ada_memory | ada_finance | ada_logs | ada_tasks | ada_decisions        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Ollama (LLM local) • Red Docker interna • Solo web-admin expuesto               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Reglas de flujo (inviolables) v0.2

- **agent-core** → solo LLM (Ollama) y envía *propuestas* a **decision-engine**. Sin reglas de negocio.
- **decision-engine** → no contiene reglas hardcodeadas. Para cada propuesta: (1) pide *simulación* a **simulation-engine**, (2) consulta *¿aprobado?* a **policy-engine**, (3) si aprobado, envía comando a **task-runner**. Es orquestador, no legislador.
- **simulation-engine** → devuelve ROI estimado, riesgo, impacto financiero y costo de infra; no ejecuta nada real.
- **policy-engine** → única fuente de reglas de gobernanza; modificable sin redeploy de otros servicios.
- **task-runner** → ejecuta solo órdenes ya aprobadas (policy-engine + decision-engine). Antes y después de ejecutar: **logging-system** con acknowledgement obligatorio; si el log falla, se cancela/revierte la ejecución según diseño.
- **logging-system** → acepta eventos con **blocking acknowledgement**; si no confirma, el flujo que emitió el evento debe abortar o no continuar.

---

## 2. Nuevo diagrama de flujo (de intención a ejecución)

```
  HUMANO
     │
     ▼
┌─────────────┐     entrada      ┌─────────────┐     propuesta     ┌─────────────────┐
│ web-admin   │ ───────────────► │ agent-core  │ ─────────────────► │ decision-engine │
└─────────────┘                  └─────────────┘                   └────────┬────────┘
                     │                                    │                  │
                     │ contexto (lectura)                 │                  │ 1. Solicitar
                     ▼                                    │                  │    simulación
              ┌─────────────┐                             │                  ▼
              │ memory (API)│                             │           ┌─────────────────┐
              │ ada_memory  │                             │           │ simulation-     │
              └─────────────┘                             │           │ engine          │
                                                          │           └────────┬────────┘
                                                          │                    │ ROI, riesgo,
                                                          │                    │ impacto fin.,
                                                          │                    │ costo infra
                                                          │                    ▼
                                                          │           ┌─────────────────┐
                                                          │           │ policy-engine  │
                                                          │           │ ¿Aprobar según │
                                                          │    2.─────►│ reglas?        │
                                                          │  consulta  └────────┬────────┘
                                                          │                    │ sí/no + motivo
                                                          │                    ▼
                                                          │           ┌─────────────────┐
                                                          │           │ logging-system  │
                                                          │    3.─────►│ (blocking ack)  │◄── Si falla:
                                                          │  decisión  └────────┬────────┘   no enviar
                                                          │                    │ ack OK      a task-runner
                                                          │                    ▼
                                                          │ 4. Si aprobado ────┼────────────►┌─────────────┐
                                                          │    comando         │            │ task-runner │
                                                          └───────────────────┼────────────└──────┬──────┘
                                                                              │                   │
                                                                              │ 5. Antes ejecutar: log (ack)
                                                                              │ 6. Ejecutar
                                                                              │ 7. Después: log resultado (ack)
                                                                              │    Si 5 o 7 fallan → cancelar/rollback
                                                                              ▼
                                                                       ┌─────────────┐
                                                                       │ financial-  │  (si aplica)
                                                                       │ ledger      │
                                                                       │ ada_finance │
                                                                       └─────────────┘
```

**Orden obligatorio:** agent-core → decision-engine → simulation-engine → policy-engine (consulta) → [logging ack] → task-runner. No se puede saltar la simulación ni la política para ejecutar en real.

---

## 3. Estructura de carpetas revisada

```
ADA/
├── docker-compose.yml
├── .env.example
├── README.md
├── ARQUITECTURA-ADA.md              # Este documento (v0.2)
│
├── agent-core/
│   ├── Dockerfile
│   └── src/
│
├── decision-engine/
│   ├── Dockerfile
│   └── src/
│
├── simulation-engine/
│   ├── Dockerfile
│   └── src/
│
├── policy-engine/
│   ├── Dockerfile
│   └── src/
│
├── task-runner/
│   ├── Dockerfile
│   └── src/
│
├── financial-ledger/                # API sobre PostgreSQL schema ada_finance
│   ├── Dockerfile
│   └── src/
│
├── memory-db/                       # API sobre PostgreSQL schema ada_memory
│   ├── Dockerfile
│   └── src/
│
├── web-admin/
│   ├── Dockerfile
│   └── src/
│
├── logging-system/                  # API + escritura a PostgreSQL schema ada_logs (blocking)
│   ├── Dockerfile
│   └── src/
│
├── shared/
│   ├── events.md
│   ├── api-contracts.md
│   └── types/
│
├── infra/                           # Definición de DB centralizada (solo esquemas/migraciones)
│   ├── postgres/
│   │   ├── schemas/
│   │   │   ├── ada_memory.sql
│   │   │   ├── ada_finance.sql
│   │   │   ├── ada_logs.sql
│   │   │   ├── ada_tasks.sql
│   │   │   └── ada_decisions.sql
│   │   └── init/                    # Scripts de creación de schemas (no datos)
│   └── backups/                     # Scripts y convenciones de backup/restore
│       ├── backup.sh
│       └── restore.sh
│
├── volumes/                         # Solo lo que no vive en PostgreSQL
│   └── ollama-data/                 # Modelos Ollama (si Ollama va en Docker)
│
└── scripts/
    ├── migrate-to-new-mac.sh        # Plan de migración a otra Mac mini
    └── health-check.sh
```

**Nota:** Ya no hay `memory-data/`, `ledger-data/` ni `logs/` como volúmenes de archivos; todo persistente va a PostgreSQL. Los volúmenes se limitan a Ollama (y opcionalmente datos binarios si más adelante se definieran).

---

## 4. Tabla final de servicios

| Servicio            | Puerto | Stateless / Stateful | Persistencia              | Dependencias |
|---------------------|--------|----------------------|---------------------------|--------------|
| **web-admin**       | 8080   | Stateless            | No                        | agent-core, decision-engine, policy-engine (lectura), logging (lectura) |
| **agent-core**      | 3001   | Stateless            | No (lee/escribe vía memory-db API) | Ollama, decision-engine, memory-db |
| **decision-engine** | 3002   | Stateless            | No (orquesta; escribe decisiones en ada_decisions vía API o logging) | simulation-engine, policy-engine, task-runner, logging-system, memory-db (lectura) |
| **simulation-engine** | 3007 | Stateless            | No                        | memory-db, financial-ledger (lectura para proyecciones) |
| **policy-engine**   | 3008   | Stateless            | Sí: reglas en BD (schema recomendado ada_policies o ada_decisions) | PostgreSQL (lectura/escritura de políticas) |
| **task-runner**     | 3003   | Stateless            | No (registra en ada_tasks vía API o logging) | decision-engine, logging-system, financial-ledger (si aplica) |
| **financial-ledger**| 3004   | Stateful (API)       | Sí: schema ada_finance    | PostgreSQL, logging-system (ack antes de confirmar operación) |
| **memory-db**       | 3005   | Stateful (API)       | Sí: schema ada_memory     | PostgreSQL, logging-system (ack en escrituras críticas) |
| **logging-system**  | 3006   | Stateful (API)       | Sí: schema ada_logs       | PostgreSQL (único escritor de ada_logs) |
| **postgres**        | 5432   | Stateful             | Volumen PG data           | Ninguno (servicio de datos) |
| **ollama**          | 11434  | Stateful (modelos)   | Volumen ollama-data       | Ninguno |

- **Stateless:** no guardan estado en disco; pueden escalar por réplicas y reiniciar sin pérdida de “memoria” (la memoria está en PostgreSQL).
- **Stateful:** mantienen o escriben estado persistente en PostgreSQL (o volúmenes); backup/restore crítico para ellos.

---

## 5. Justificación técnica de cada mejora

### 5.1 policy-engine (nuevo)

- **Problema:** Reglas en decision-engine acoplan gobernanza al código y obligan a redeploy para cambiar políticas.
- **Solución:** Servicio dedicado que contiene *todas* las reglas de gobernanza. decision-engine solo pregunta “dada esta propuesta y esta simulación, ¿está permitido?”.
- **Beneficios:** Cambio de políticas sin tocar agent-core, decision-engine ni task-runner; auditoría de “quién aprobó según qué regla”; evolución hacia autonomía controlada variando solo políticas.

### 5.2 simulation-engine (nuevo)

- **Problema:** Ejecutar en real sin estimar impacto genera riesgo operativo y financiero.
- **Solución:** Paso obligatorio antes de aprobar: simulation-engine calcula ROI estimado, riesgo, impacto financiero y costo de infra. decision-engine usa esas salidas para pedir aprobación a policy-engine y al humano (vía web-admin) si aplica.
- **Beneficios:** Menos ejecuciones erróneas; trazabilidad “qué se simuló antes de aprobar”; base para A/B o “what-if” sin tocar producción.

### 5.3 PostgreSQL centralizado (eliminar SQLite por servicio)

- **Por qué PostgreSQL es mejor elección aquí:**
  - **Un solo punto de backup/restore** para migrar a otra Mac mini: un dump de PostgreSQL vs múltiples archivos SQLite repartidos en contenedores.
  - **Transacciones cross-schema:** se puede escribir en ada_logs y ada_finance en la misma transacción (logging + asiento contable), garantizando consistencia.
  - **Concurrencia y robustez:** PostgreSQL maneja múltiples conexiones desde varios servicios sin riesgo de lock de archivo ni corrupción típica de SQLite en entornos multiwriter.
  - **Esquemas separados (ada_memory, ada_finance, ada_logs, ada_tasks, ada_decisions):** aislamiento lógico, permisos por schema y crecimiento independiente sin “una base por servicio” dispersa.
  - **Evolución:** mismo motor en Mac mini M1 y en una Mac más potente; se escala con más CPU/RAM o réplicas de lectura sin cambiar arquitectura.

### 5.4 Logging con blocking acknowledgement (no fire-and-forget)

- **Problema:** Si logging es fire-and-forget, una ejecución puede completarse sin quedar registrada; se pierde integridad de auditoría.
- **Solución:** Cualquier paso que deba quedar auditado llama a logging-system y **espera confirmación** (HTTP 200 + id de evento o equivalente). Si logging-system no responde o falla, el llamador **cancela o no confirma** la acción (p. ej. task-runner no marca tarea como “ejecutada” hasta tener ack del log).
- **Integridad de auditoría:** “Nunca hay ejecución exitosa sin log exitoso”. Patrón: (1) Escribir en ada_logs en la misma transacción que el cambio de estado (si un solo servicio escribe ambos), o (2) Primero log (ack), luego ejecución; si ejecución falla, se registra un segundo evento de fallo. Así el registro es el contrato de verdad.

### 5.5 Stateless vs stateful y estrategia de backup/restore

- **Stateless:** agent-core, decision-engine, simulation-engine, policy-engine (si solo lee/escribe en PostgreSQL y no mantiene caché crítico), task-runner, web-admin. Reinicio o migración no requieren restaurar estado de estos servicios; solo asegurar que PostgreSQL y Ollama estén disponibles y restaurados.
- **Stateful:** postgres (datos), logging-system (ada_logs), memory-db (ada_memory), financial-ledger (ada_finance), ollama (modelos). Backup prioritario: **PostgreSQL** (todos los schemas) y **volumen de Ollama**.
- **Estrategia backup/restore para migración:** Backups periódicos de PostgreSQL (pg_dump o lógico) y copia del volumen de Ollama. En la nueva Mac mini: instalar Docker, restaurar volúmenes/backups, levantar el mismo docker-compose; los servicios stateless no tienen “estado que restaurar”.

### 5.6 Comunicación interna: REST vs message broker (MVP vs escalabilidad)

- **Opción A — Solo HTTP REST (recomendado para MVP):**
  - Menos componentes: no Redis ni RabbitMQ.
  - Depuración simple: un request = una respuesta.
  - Flujo síncrono natural: decision-engine llama a simulation → policy → task-runner en secuencia; el “blocking ack” de logging encaja con llamadas síncronas.
  - Menor latencia en flujos cortos y menos puntos de fallo.

- **Opción B — Message broker (Redis/RabbitMQ):**
  - Útil cuando haya alta carga, colas de decisiones pendientes o necesidad de reintentos/desacoplo temporal.
  - Añade complejidad operativa (persistencia del broker, monitoreo) y otro componente a respaldar en migración.

- **Justificación para fase inicial:** Usar **solo HTTP REST** entre servicios. Mantener la posibilidad de introducir un broker más adelante entre agent-core → decision-engine o decision-engine → task-runner si aparece necesidad de colas o procesamiento asíncrono, sin cambiar la responsabilidad de cada servicio.

---

## 6. Riesgos técnicos actualizados

| Riesgo | Mitigación |
|--------|------------|
| **PostgreSQL como único punto de fallo** | Backup automático (cron + pg_dump); en migración, restaurar antes de levantar servicios. Opcional: réplica de solo lectura en Mac más potente. |
| **Logging bloqueante aumenta latencia y acopla disponibilidad** | Timeout corto en cliente (ej. 3–5 s); si logging-system no responde, abortar y reintentar después; no “ejecutar sin log”. Mantener logging-system estable y monitoreado. |
| **policy-engine mal configurado (reglas incorrectas)** | Versionado de políticas en BD; web-admin para edición con revisión; opcional: entorno de “staging” de políticas antes de producción. |
| **simulation-engine desalineado con realidad** | Modelos de simulación documentados y revisables; comparar periódicamente predicciones vs resultados reales (ada_tasks / ada_finance) y ajustar. |
| **Ollama en M1 (Docker vs host)** | Probar en host con `host.docker.internal:11434`; si va en Docker, límites de memoria y volumen para modelos; documentar en README. |
| **Migración a otra Mac mini: diferencias de red/nombres** | Usar nombres de servicio Docker (no IPs); mismo docker-compose y .env; solo cambiar recursos (CPU/memoria) si hace falta. |
| **Escalación futura con más autonomía** | Controlar todo en policy-engine (umbrales, modos); decision-engine solo aplica; no añadir lógica de “excepción” en task-runner ni agent-core. |

---

## 7. Plan de migración futura a Mac mini más potente

1. **Preparación en Mac actual (origen)**  
   - Ejecutar backup de PostgreSQL (todos los schemas) y copia del volumen/archivos de Ollama.  
   - Documentar versión de Docker Compose y variables de entorno (.env).

2. **En la nueva Mac mini (destino)**  
   - Instalar Docker (y Docker Compose).  
   - Copiar proyecto ADA (código + docker-compose + .env).  
   - Restaurar backup de PostgreSQL en un volumen o contenedor Postgres inicial.  
   - Restaurar datos de Ollama en el volumen que use el servicio Ollama.

3. **Arranque**  
   - `docker-compose up -d`. Los servicios stateless arrancan sin estado; los que dependen de PostgreSQL y Ollama usan los datos restaurados.

4. **Validación**  
   - Comprobar que web-admin responde, que agent-core puede llamar a Ollama y que una decisión de prueba pasa por simulation-engine → policy-engine → logging (ack) y, si aplica, task-runner.  
   - Revisar ada_logs y ada_decisions para confirmar que no hay huecos tras la migración.

5. **Opcional (Mac más potente)**  
   - Aumentar recursos en docker-compose (CPU/memoria) para Postgres y Ollama.  
   - Considerar réplica de lectura de PostgreSQL si se añaden cargas analíticas.

Con esto, la arquitectura v0.2 queda centrada en **robustez** (PostgreSQL, logging con ack), **gobernanza** (policy-engine, sin reglas en decision-engine) y **evolución hacia autonomía controlada** (simulación obligatoria y políticas modificables sin redeploy).  
Cuando quieras pasar a implementación, se puede hacer por fases: primero Postgres + schemas + logging-system + policy-engine, luego decision-engine + simulation-engine, después agent-core y task-runner, y por último web-admin.
