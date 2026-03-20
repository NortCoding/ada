"""
Business engine for ADA CLI.

Purpose:
Allow ADA to identify realistic income opportunities (practical, low-risk),
rank them, suggest small microproducts, and generate a concrete action plan
aligned with the project's roadmap.

Important:
- No income simulation. We only propose ways to create verifiable value.
- Keep it simple and functional with heuristics + optional LLM.
"""

from __future__ import annotations

import os
import re
import json
import urllib.request
from typing import Any, Dict, List, Optional


def _has_module(path: str) -> bool:
    base_path = os.getcwd()
    full_path = os.path.join(base_path, path)
    return os.path.exists(full_path)


def _capabilities_snapshot() -> Dict[str, bool]:
    # Best-effort: infer capabilities by local file existence.
    return {
        "cli_analyze": True,
        "cli_list_files": True,
        "cli_create_file": True,
        "cli_fix_error_diff": True,
        "cli_run_execute": _has_module("ada/tools/shell_tools.py"),
        "debug_engine": _has_module("ada/core/debug_engine.py"),
        "roadmap_engine": _has_module("ada/core/roadmap_engine.py"),
    }


def find_opportunities(context: str) -> List[Dict[str, Any]]:
    """
    Analyze current ADA capabilities (and roadmap hints) and identify realistic
    opportunities to generate value or income.

    Returns a list of opportunities, each as a dict with simple attributes.
    """
    _ = context
    caps = _capabilities_snapshot()

    # Heuristic opportunities: small digital products & service-like offers.
    # Keep them aligned with what ADA can already do (tools, debugging, templates).
    base_opps: List[Dict[str, Any]] = []

    # Opportunity 1: "DevOps/debug starter kit" as templates + scripts.
    base_opps.append(
        {
            "id": "kit_debug_cli",
            "title": "Debugging starter kit (templates + ADA CLI playbooks)",
            "speed": 9,
            "difficulty": 4,
            "revenue_potential": 7,
            "alignment": 9,
            "why": "Fast to package: concrete playbooks + repeatable commands + example artifacts.",
            "requires": [
                "write 5-10 example files/templates",
                "document commands and expected outputs",
                "include verification steps (tests/run) as evidence",
            ],
        }
    )

    # Opportunity 2: "CLI automation snippets" (sell as gists/mini packages).
    base_opps.append(
        {
            "id": "cli_automation_snippets",
            "title": "CLI automation snippets (create/fix/analyze/run) as mini package",
            "speed": 8,
            "difficulty": 5,
            "revenue_potential": 6,
            "alignment": 8,
            "why": "Directly leverages existing CLI primitives: read/write/analyze/fix/diff/confirm/run.",
            "requires": [
                "package examples",
                "ensure commands are deterministic",
                "add short docs for safe execution",
            ],
        }
    )

    # Opportunity 3: "Roadmap-driven productization templates".
    base_opps.append(
        {
            "id": "roadmap_to_tasks",
            "title": "Roadmap-to-tasks workflow template (what next / improve yourself)",
            "speed": 7,
            "difficulty": 4,
            "revenue_potential": 5,
            "alignment": 7,
            "why": "Matches the strategic layer we built: proposals from roadmap without auto-execution.",
            "requires": [
                "create a template doc for users",
                "include examples of 'proposal-only' evolution",
                "add a checklist for human approval",
            ],
        }
    )

    # Slightly adapt if some capabilities are missing.
    if not caps.get("cli_run_execute"):
        for opp in base_opps:
            if opp["id"] == "kit_debug_cli":
                opp["alignment"] = max(1, opp["alignment"] - 2)

    return base_opps


def score_opportunities(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank opportunities by:
    - speed
    - difficulty (inverse)
    - revenue potential
    - alignment with ADA goals
    """
    def _score(o: Dict[str, Any]) -> float:
        # Normalize difficulty inversion: higher difficulty -> lower score.
        # All values are assumed 1..10.
        speed = float(o.get("speed", 0))
        difficulty = float(o.get("difficulty", 10))
        revenue = float(o.get("revenue_potential", 0))
        alignment = float(o.get("alignment", 0))
        return (0.3 * speed) + (0.25 * (10 - difficulty)) + (0.25 * revenue) + (0.2 * alignment)

    scored = []
    for o in opportunities:
        o2 = dict(o)
        o2["score"] = _score(o2)
        scored.append(o2)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def suggest_microproducts(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Suggest small tools/utility scripts/templates/services aligned with top opportunities.
    """
    top = opportunities[:3]
    microproducts: List[Dict[str, Any]] = []

    for opp in top:
        if opp["id"] == "kit_debug_cli":
            microproducts.extend(
                [
                    {
                        "opportunity_id": opp["id"],
                        "title": "Playbook: 'fix error' from error text → DIFF → apply",
                        "deliverable": "Markdown + example commands + example diff output",
                    },
                    {
                        "opportunity_id": opp["id"],
                        "title": "Example pack: testOpt scenarios",
                        "deliverable": "A small folder with broken scripts and their fixed versions",
                    },
                ]
            )
        elif opp["id"] == "cli_automation_snippets":
            microproducts.extend(
                [
                    {
                        "opportunity_id": opp["id"],
                        "title": "Mini package: safe runner wrappers",
                        "deliverable": "A set of small shell/prompt snippets for 'run' with confirmation",
                    },
                    {
                        "opportunity_id": opp["id"],
                        "title": "Templates: create file with content + verify",
                        "deliverable": "Examples + docs showing deterministic file writes and sizes",
                    },
                ]
            )
        else:
            microproducts.extend(
                [
                    {
                        "opportunity_id": opp["id"],
                        "title": "Template doc: roadmap → what next → proposal log",
                        "deliverable": "A one-page template + example output screenshots/text",
                    }
                ]
            )

    return microproducts


def generate_action_plan(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create concrete steps to build and test the opportunity.
    Keep it simple: build artifacts, document expected outputs, add verification steps.
    """
    title = opportunity.get("title", "Opportunity")
    opp_id = opportunity.get("id", "unknown")

    steps: List[Dict[str, Any]] = []
    steps.append({"step": 1, "action": "Define the exact deliverables (files + docs) and acceptance criteria."})
    steps.append({"step": 2, "action": "Use ADA CLI to generate/prepare example artifacts (create/analyze/fix/run)."})
    steps.append({"step": 3, "action": "Add deterministic verification commands (e.g. run python ... and expect exit=0)."})
    steps.append({"step": 4, "action": "Write proof-of-work: expected outputs (DIFF, sizes, summaries) in README."})
    steps.append({"step": 5, "action": "Create a distribution plan: publish as repo/artifact and collect feedback via a small call-to-action."})

    return {
        "opportunity_id": opp_id,
        "title": title,
        "action_plan": steps,
        "human_approval": True,  # We keep the no-auto-change rule.
        "notes": "Focus on practical execution; no auto-apply beyond confirmation in CLI.",
    }

