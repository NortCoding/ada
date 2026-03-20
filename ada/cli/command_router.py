"""
Command router for the ADA CLI.

Keep it simple and deterministic:
- Parse the terminal input text
- Route to concrete CLI handlers (no AI yet)
"""

from __future__ import annotations

import sys


def route_command(input_text: str) -> None:
    cmd = (input_text or "").strip().lower()
    if not cmd:
        return

    # Helper: best-effort "what to build next" without executing anything.
    def _print_roadmap_and_next() -> None:
        from ada.core.roadmap_engine import get_current_phase, get_current_goals, load_roadmap

        roadmap_text = load_roadmap()
        phase = get_current_phase(roadmap_text)
        goals = get_current_goals(roadmap_text)

        print(f"Current phase: {phase}")
        if goals:
            print("Current goals:")
            for g in goals:
                print(f"- {g}")
        else:
            print("Current goals: (none parsed)")

    def _normalize_python_cmd(s: str) -> str:
        # In this environment `python` may not exist; prefer `python3`.
        parts = (s or "").strip().split(None, 1)
        if not parts:
            return s
        if parts[0] == "python":
            if len(parts) == 1:
                return "python3"
            return "python3 " + parts[1]
        return s

    def _business_context() -> str:
        from ada.core.roadmap_engine import load_roadmap
        roadmap_text = load_roadmap()
        return f"roadmap:\n{roadmap_text[:4000]}"

    def _find_opportunities_print() -> None:
        from ada.core.business_engine import (
            find_opportunities,
            score_opportunities,
            suggest_microproducts,
        )

        context = _business_context()
        opps = find_opportunities(context)
        scored = score_opportunities(opps)

        micro = suggest_microproducts(scored)

        print("Business opportunities (ranked):")
        for i, o in enumerate(scored[:3], start=1):
            print(f"\n{i}. {o.get('title')}")
            print(f"   score={o.get('score'):.2f}")
            print(f"   speed={o.get('speed')} difficulty={o.get('difficulty')} revenue={o.get('revenue_potential')} alignment={o.get('alignment')}")
            print(f"   why: {o.get('why')}")

        print("\nMicroproducts to build next:")
        for m in micro:
            print(f"- {m.get('title')}")
            print(f"  deliverable: {m.get('deliverable')}")

    def _create_business_plan_print() -> None:
        from ada.core.business_engine import (
            find_opportunities,
            score_opportunities,
            generate_action_plan,
        )

        context = _business_context()
        opps = find_opportunities(context)
        scored = score_opportunities(opps)

        top = scored[0] if scored else {}
        plan = generate_action_plan(top)

        print("Business plan (top opportunity):")
        print(f"- {plan.get('title')}")
        for s in plan.get("action_plan", []):
            print(f"Step {s.get('step')}: {s.get('action')}")
        print("\nHuman approval required:")
        print(str(plan.get("human_approval", True)))

    if cmd in {"find business opportunities", "find business opportunity"} or cmd.startswith(
        "find business opportunities"
    ):
        _find_opportunities_print()
        return

    if cmd in {"generate product ideas", "what can we sell", "what can we sell?"} or cmd.startswith(
        "generate product ideas"
    ):
        _find_opportunities_print()
        return

    if cmd in {"create a business plan", "create business plan"} or cmd.startswith("create a business plan"):
        _create_business_plan_print()
        return

    if cmd == "roadmap":
        # Minimal roadmap summary (no complex parsing).
        roadmap_text = __import__("ada.core.roadmap_engine", fromlist=["load_roadmap"]).load_roadmap()
        print(roadmap_text[:4000])
        return

    if cmd == "what next":
        _print_roadmap_and_next()
        return

    if cmd == "what should i build next" or cmd == "what should i build next?":
        from ada.core.roadmap_engine import load_roadmap, get_current_phase
        from ada.core.task_planner import suggest_tasks

        roadmap_text = load_roadmap()
        phase = get_current_phase(roadmap_text)

        current_state = (
            f"phase={phase}; "
            "cli_has_analyze=list/files/summary; "
            "cli_has_fix=diff+confirm+apply; "
            "cli_has_run_execute=confirmed; "
            "auto_apply_fixes=disabled"
        )
        tasks = suggest_tasks(roadmap_text, current_state)

        print("Proposed actions:")
        for i, t in enumerate(tasks, start=1):
            print(f"{i}. {t}")
        print("\nNext step:")
        print("Implement the first proposed task (no automatic execution yet).")
        return

    if cmd == "improve yourself" or cmd == "improve yourself.":
        from ada.core.roadmap_engine import load_roadmap, get_current_phase
        from ada.core.task_planner import suggest_tasks
        from ada.memory.progress import log_progress

        roadmap_text = load_roadmap()
        phase = get_current_phase(roadmap_text)

        # Lightweight state: based on what exists in the workspace.
        # (No complex scanning; deterministic heuristics.)
        current_state = (
            f"phase={phase}; "
            "cli_has_analyze=list/files; "
            "cli_has_create=write_file; "
            "cli_has_fix=diff+confirm; "
            "cli_has_run_execute=confirmed; "
            "git_tools=not_implemented_yet; "
            "auto_apply_fixes=disabled"
        )

        tasks = suggest_tasks(roadmap_text, current_state)

        print("Analysis:")
        print("CLI working; improvements needed for verification loop and development workflow.")
        print("\nProposed actions:")
        for i, t in enumerate(tasks, start=1):
            print(f"{i}. {t}")
        print("\nNext step:")
        print("Implement the first proposed task (no automatic execution yet).")

        print("\nApply this evolution now? (y/n): n (auto-no, by rule)")

        # Record that we proposed evolution (not applied).
        try:
            res = "Proposed actions: " + " | ".join(tasks)
            log_progress("improve yourself (proposal only)", res)
        except Exception:
            pass
        return

    if "list files" in cmd:
        from ada.tools.file_tools import list_files as tool_list_files

        tool_list_files(".")
        return

    if "analyze" in cmd:
        analyze_project()
        return

    if "fix" in cmd:
        fix_project(input_text)
        return

    if "create" in cmd:
        create_project(input_text)
        return

    if "cycle" in cmd or "selftest" in cmd or "test cycle" in cmd:
        run_cycle_test()
        return

    if cmd.startswith("run "):
        from ada.tools.shell_tools import run_command

        shell_cmd = input_text[len(input_text.split(None, 1)[0]) :].strip()
        if not shell_cmd:
            print("TODO: run <command> (missing command)")
            return

        shell_cmd = _normalize_python_cmd(shell_cmd)

        print(f"Command to execute:\n{shell_cmd}")
        apply_choice = "n"
        if sys.stdin is not None and getattr(sys.stdin, "isatty", None) and sys.stdin.isatty():
            apply_choice = input("Execute? (y/n): ").strip().lower()
        else:
            try:
                import select

                ready, _, _ = select.select([sys.stdin], [], [], 0)
                if ready:
                    apply_choice = sys.stdin.readline().strip().lower() or "n"
            except Exception:
                apply_choice = "n"

        if apply_choice == "y":
            output = run_command(shell_cmd)
            print("\n=== COMMAND OUTPUT ===\n")
            print(output)
        else:
            print("Execution cancelled.")
        return

    if cmd.startswith("execute "):
        # Alias: execute <command>
        from ada.tools.shell_tools import run_command

        # Keep exact substring after the first token.
        shell_cmd = input_text[len(input_text.split(None, 1)[0]) :].strip()
        if not shell_cmd:
            print("TODO: execute <command> (missing command)")
            return

        shell_cmd = _normalize_python_cmd(shell_cmd)

        print(f"Command to execute:\n{shell_cmd}")
        apply_choice = "n"
        if sys.stdin is not None and getattr(sys.stdin, "isatty", None) and sys.stdin.isatty():
            apply_choice = input("Execute? (y/n): ").strip().lower()
        else:
            try:
                import select

                ready, _, _ = select.select([sys.stdin], [], [], 0)
                if ready:
                    apply_choice = sys.stdin.readline().strip().lower() or "n"
            except Exception:
                apply_choice = "n"

        if apply_choice == "y":
            output = run_command(shell_cmd)
            print("\n=== COMMAND OUTPUT ===\n")
            print(output)
        else:
            print("Execution cancelled.")
        return

    print("Unknown command")


def run_cycle_test() -> None:
    """
    FASE 1 "ciclo completo verificable":
    - read: analizamos el directorio (resumen)
    - write: persistimos un resultado en un archivo
    - run: ejecutamos un comando shell controlado
    - debug: ejecutamos un comando que falla y capturamos el resultado
    """
    import json
    from pathlib import Path

    from ada.core.code_analyzer import summarize_current_directory
    from ada.core.shell_executor import run_shell_command

    project_root = "."
    print("== ADA CLI CYCLE TEST: read -> write -> run -> debug ==")

    # READ
    summary = summarize_current_directory(project_root)
    print(f"[read] files={summary['number_of_files']}")

    # WRITE
    out_dir = Path("ada") / "cli" / "cycle_test"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "latest.json"

    run_ok = run_shell_command('python3 -c "print(\'RUN_OK\')"')
    run_fail = run_shell_command('python3 -c "import sys; sys.exit(2)"')

    payload = {
        "stage_read": summary,
        "stage_run": {
            "command": run_ok.command,
            "returncode": run_ok.returncode,
            "stdout": run_ok.stdout.strip(),
            "stderr": run_ok.stderr.strip(),
        },
        "stage_debug": {
            "command": run_fail.command,
            "returncode": run_fail.returncode,
            "stdout": run_fail.stdout.strip(),
            "stderr": run_fail.stderr.strip(),
        },
    }
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[write] wrote {out_file.as_posix()}")

    # DEBUG (básico): confirmamos que el fallo fue realmente capturado
    if run_fail.returncode != 2:
        print("[debug] unexpected failure behavior")
    else:
        print("[debug] failure captured as expected (returncode=2)")

    print("== END CYCLE TEST ==")


def analyze_project() -> None:
    # Real implementation lives in `ada/core/code_analyzer.py`.
    from ada.core.code_analyzer import analyze_project as core_analyze_project

    core_analyze_project(".")


def fix_project(command: str) -> None:
    # Minimal "real" fix: handle the "fix error" directive deterministically.
    cmd_raw = (command or "").strip()
    cmd = cmd_raw.lower()

    # Phase 1 deterministic fix: `fix error` (exactly)
    if cmd in {"fix error", "fix-error"}:
        from ada.core.file_ops import fix_error

        fixed_path = fix_error("error.txt")
        print(f"Fixed error in {fixed_path}")
        return

    # Debug engine: `fix error <error text>`
    # Expected: "fix error File test.py line 10 NameError: ..."
    if cmd.startswith("fix error ") or cmd.startswith("fix-error "):
        import sys

        from ada.core.debug_engine import analyze_error, apply_fix, show_diff, suggest_fix

        # Keep original text after the prefix for better matching.
        prefix_len = len("fix error ") if cmd.startswith("fix error ") else len("fix-error ")
        error_text = cmd_raw[prefix_len:].strip()

        info = analyze_error(error_text)
        if not info.get("exists"):
            print("\nCannot propose fix: file not found.\n")
            return

        original = info.get("content", "")
        modified = suggest_fix(error_text, original)

        show_diff(original, modified)

        # Confirm before writing (REGLA CLAVE).
        apply_choice = "n"
        if sys.stdin is not None and getattr(sys.stdin, "isatty", None) and sys.stdin.isatty():
            apply_choice = input("\nApply this fix? (y/n): ").strip().lower()
        else:
            # Non-interactive mode: try to read a piped answer without blocking.
            try:
                import select

                ready, _, _ = select.select([sys.stdin], [], [], 0)
                if ready:
                    apply_choice = sys.stdin.readline().strip().lower() or "n"
            except Exception:
                apply_choice = "n"

        if apply_choice == "y":
            res = apply_fix(info.get("file_path"), modified)
            print(f"\nFix applied. {res.get('success_message','')}\n")
        else:
            print("\nFix cancelled (no changes written).\n")
        return

    print("TODO: fix (no handler for this specific instruction)")


def create_project(command: str) -> None:
    # Minimal "real" create: handle "create file <path>".
    cmd = (command or "").strip()
    cmd_lower = cmd.lower()
    lower_tokens = cmd_lower.split()

    if len(lower_tokens) >= 3 and lower_tokens[0] == "create" and lower_tokens[1] == "file":
        # Supported syntax:
        # - create file <path>
        # - create file <path> with content <content>
        #
        # We parse using case-insensitive markers but preserve original substrings.
        from ada.tools.file_tools import write_file

        # Split by the marker "with content" (if present).
        marker = "with content"
        if marker in cmd_lower:
            before, after = cmd_lower.split(marker, 1)
            before_real = cmd[: len(before)]
            after_real = cmd[len(before) + len(marker) :].strip()

            # before_real should end with the path segment after "create file".
            # Example: "create file test.txt " (note trailing space) -> extract "test.txt"
            path_segment = before_real.split("file", 1)[1].strip()
            content = after_real
            if not path_segment:
                print("TODO: create file (missing path)")
                return

            res = write_file(path_segment, content)
            file_display = path_segment.split("/")[-1].split("\\")[-1]
            print(f"File created: {file_display}")
            print(f"Size: {res['size_bytes']} bytes")
            return

        # Fallback: create file <path>
        path = cmd.split("file", 1)[1].strip()
        if not path:
            print("TODO: create file (missing path)")
            return

        # Overwrite even if exists, to avoid "falso éxito".
        default_content = f"Created by ADA CLI at {__import__('datetime').datetime.utcnow().isoformat()}Z\n"
        res = write_file(path, default_content)
        file_display = path.split("/")[-1].split("\\")[-1]
        print(f"File created: {file_display}")
        print(f"Size: {res['size_bytes']} bytes")
        return

    print("TODO: create (no handler for this specific instruction)")

