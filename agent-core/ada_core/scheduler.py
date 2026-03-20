"""
ADA v2 Autonomous — Scheduler (bucle cognitivo completo).
1 load goals 2 memories 3 research 4 ideas 5 evaluate 6 store opportunities
7 select best opportunities 8 create action plans 9 store experiences
10 generate derived goals. Never crashes; logs failures and continues.
"""
import logging
import threading
import time

from ada_core.memory_manager import MemoryManager
from ada_core.reasoning_engine import reason_about
from ada_core.research_engine import research_goal
from ada_core.opportunity_engine import evaluate_and_score_idea
from ada_core.strategy_engine import StrategyEngine
from ada_core.decision_engine import (
    select_best_opportunities,
    create_action_plan,
    generate_derived_goals,
    evaluate_experience,
)
from ada_core.execution_planner import create_and_store_plan

LOG = logging.getLogger(__name__)
INTERVAL_SEC = int(__import__("os").getenv("ADA_SCHEDULER_INTERVAL_SEC", "1800"))


def _load_related_memories(goal_text: str, memory: MemoryManager, limit: int = 5) -> str:
    """Carga memorias recientes relacionadas."""
    memories = memory.get_recent_memories(limit=limit)
    if not memories:
        return ""
    parts = []
    for m in memories:
        topic = m.get("topic") or ""
        content = (m.get("content") or "")[:300]
        if content:
            parts.append(f"[{topic}] {content}")
    return "\n".join(parts) if parts else ""


def _run_cognitive_cycle() -> None:
    """
    Bucle completo:
    1 load active goals
    2 load related memories
    3 research_goal
    4 generate ideas
    5 evaluate ideas
    6 store opportunities
    7 decision_engine selects best opportunities
    8 create action plans, store experiences (with optional evaluate_experience -> learning)
    9 generate derived goals if applicable
    """
    try:
        memory = MemoryManager()
        strategy = StrategyEngine()
        goals = strategy.get_active_goals()
        if not goals:
            return

        for goal in goals:
            goal_id = goal.get("id")
            goal_text = goal.get("goal") or ""
            if not goal_text:
                continue
            try:
                # 1–2) Context
                context = _load_related_memories(goal_text, memory)

                # 3) Research
                analysis = research_goal(goal_text, context)
                if analysis:
                    memory.add_experience(
                        event=f"research_goal:{goal_text[:100]}",
                        result=analysis[:500],
                        learning="Análisis para generar oportunidades",
                    )

                # 4–6) Ideas → evaluate → store opportunities
                ideas = strategy.think_about_goal(goal)
                for idea in (ideas or [])[:5]:
                    try:
                        evaluated = evaluate_and_score_idea(idea, goal_id=goal_id, goal_text=goal_text)
                        memory.store_opportunity(
                            idea=evaluated["idea"],
                            score=evaluated["score"],
                            impact=evaluated["impact"],
                            ease=evaluated["ease"],
                            speed=evaluated["speed"],
                            risk=evaluated["risk"],
                            goal_id=goal_id,
                            status="pending",
                        )
                        LOG.info("scheduler: opportunity stored score=%.2f goal_id=%s", evaluated["score"], goal_id)
                    except Exception as e:
                        LOG.warning("scheduler: evaluate idea failed: %s", e)
                        strategy.store_ideas(goal_id, [idea], 0)

                # 10) Derived goals from this goal + its ideas
                try:
                    recent_ideas = [o["idea"] for o in memory.get_opportunities(goal_id=goal_id, limit=10)]
                    if recent_ideas:
                        n_derived = generate_derived_goals(goal, recent_ideas, memory)
                        if n_derived:
                            LOG.info("scheduler: generated %d derived goals for goal_id=%s", n_derived, goal_id)
                except Exception as e:
                    LOG.warning("scheduler: derived goals failed: %s", e)

            except Exception as e:
                LOG.warning("scheduler: goal id=%s failed: %s", goal_id, e)

        # 7–11) Select best opportunities, create plans (action_plans + experiences), store learning
        try:
            best = select_best_opportunities(memory)
            for opp in best:
                try:
                    out = create_and_store_plan(opp, memory=memory, store_as_experience=True)
                    if out:
                        LOG.info("scheduler: action plan stored for opportunity id=%s", opp.get("id"))
                except Exception as e:
                    LOG.warning("scheduler: create plan failed: %s", e)
        except Exception as e:
            LOG.warning("scheduler: decision/plans step failed: %s", e)

    except Exception as e:
        LOG.warning("scheduler cognitive cycle failed: %s", e)


def _loop() -> None:
    while True:
        try:
            _run_cognitive_cycle()
        except Exception as e:
            LOG.warning("scheduler loop: %s", e)
        time.sleep(INTERVAL_SEC)


def start_scheduler() -> None:
    """Arranca el bucle cognitivo en un hilo daemon."""
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    LOG.info("ADA v2 Autonomous scheduler started (interval=%ds)", INTERVAL_SEC)
