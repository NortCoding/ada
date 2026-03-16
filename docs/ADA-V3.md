# ADA v3 — Operational Autonomous Cognitive Agent

ADA v3 extends v2.5 into a **complete cognitive agent** that thinks, decides, plans, learns, and evolves.

## Capabilities

- **Analyze goals** — Research and context loading
- **Generate ideas** — Strategy engine from goals
- **Evaluate opportunities** — Score (impact, ease, speed, risk)
- **Choose best ones** — `decision_engine.select_best_opportunities` (score ≥ 7.5, top 3)
- **Create actionable plans** — `execution_planner.create_and_store_plan` → `action_plans` + experiences
- **Generate new goals** — `goal_generation_engine` / `derived_goals` table
- **Learn from experiences** — `evaluate_experience()` → learning stored in experiences
- **Evolve strategies** — Scheduler runs full cognitive loop every `ADA_SCHEDULER_INTERVAL_SEC`

## New modules (v3)

| Module | Role |
|--------|------|
| **decision_engine** | Select best opportunities, create_action_plan, generate_derived_goals, evaluate_experience |
| **execution_planner** | create_and_store_plan (plan → action_plans + experience with learning) |
| **goal_generation_engine** | Wrapper for derived goal generation, get_active_derived_goals |

## Database (v3)

- **ada_core.action_plans**: `id`, `opportunity_id`, `plan`, `status`, `created_at`
- **ada_core.derived_goals**: (existing) `id`, `parent_goal_id`, `goal`, `status`, `created_at`
- **ada_core.experiences**: (extended) `success_score`, `evaluation`

Schema file: `infra/postgres/schemas/ada_core_v3.sql` (run after ada_core.sql and ada_core_v2_autonomous.sql).

## API v3

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v3/opportunities/top` | Top scored opportunities |
| GET | `/v3/goals/derived` | Derived goals (`?parent_goal_id=&status=active`) |
| GET | `/v3/plans` | Action plans (from table or experiences) |
| GET | `/v3/learning` | Recent learnings (experiences with learning/evaluation) |
| POST | `/v3/chat/structured` | Chat with structured response (Analysis, Proposal, Risks, Next Step) |
| POST | `/v3/research` | Research goal; body: `{"goal": "...", "context": "..."}` |

## Structured response format

Responses use the following sections:

- **Analysis** — Explanation of the situation or idea
- **Proposal** — Concrete ideas or recommendations
- **Risks** — Possible problems or caveats
- **Next Step** — One concrete next action

Controlled via `conversation_engine.ADA_STRUCTURED_RESPONSE_FORMAT`.

## Cognitive loop (scheduler)

1. Load active goals  
2. Load related memories  
3. Research goal  
4. Generate ideas  
5. Evaluate and store opportunities  
6. Generate derived goals per goal  
7. Select best opportunities (score ≥ threshold, top N)  
8. Create action plans (`execution_planner`), store in `action_plans` + experiences  
9. Evaluate experience → store learning  
10. Loop continues; next cycle after `ADA_SCHEDULER_INTERVAL_SEC`

## Resilience

- Empty tables → endpoints return `[]` or safe defaults
- Ollama/memory failures → try/except, log and continue with next goal/opportunity
- Scheduler never exits on single failure

## Performance

- **Mac Mini M1, 16GB RAM** — Supported
- **Ollama**: default `llama3:8b`, fallback `qwen2:7b` (env: `OLLAMA_MODEL`, `OLLAMA_FALLBACK_MODEL`)

Existing v2 endpoints remain; v3 adds the new namespace and behaviour without removing prior functionality.
