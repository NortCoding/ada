# ADA v2.5 / v3 — internal modules (agente cognitivo autónomo)
from ada_core.reasoning_engine import reason_about
from ada_core.conversation_engine import ConversationEngine, ADA_SYSTEM_PROMPT_V2, ADA_STRUCTURED_RESPONSE_FORMAT
from ada_core.memory_manager import MemoryManager
from ada_core.strategy_engine import StrategyEngine
from ada_core.scheduler import start_scheduler
from ada_core.research_engine import research_goal, compare_options, evaluate_tools
from ada_core.opportunity_engine import score_opportunity, evaluate_and_score_idea
from ada_core.self_improvement_engine import analyze_system_bottlenecks, suggest_prompt_improvements, analyze_recent_errors
from ada_core.decision_engine import select_best_opportunities, create_action_plan, generate_derived_goals, evaluate_experience
from ada_core.execution_planner import create_and_store_plan, plan_for_top_opportunities
from ada_core.goal_generation_engine import generate_derived_goals as generate_derived_goals_v3, get_active_derived_goals

__all__ = [
    "reason_about",
    "ConversationEngine",
    "ADA_SYSTEM_PROMPT_V2",
    "ADA_STRUCTURED_RESPONSE_FORMAT",
    "MemoryManager",
    "StrategyEngine",
    "start_scheduler",
    "research_goal",
    "compare_options",
    "evaluate_tools",
    "score_opportunity",
    "evaluate_and_score_idea",
    "analyze_system_bottlenecks",
    "suggest_prompt_improvements",
    "analyze_recent_errors",
    "select_best_opportunities",
    "create_action_plan",
    "generate_derived_goals",
    "evaluate_experience",
    "create_and_store_plan",
    "plan_for_top_opportunities",
    "generate_derived_goals_v3",
    "get_active_derived_goals",
]
