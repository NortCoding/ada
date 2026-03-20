"""
Validación estricta de planes (rutas, LIST_DIR, señales de contaminación).

Ejecutar en contenedor o con Python 3.9+:
  cd agent-core && PYTHONPATH=src python -m pytest tests/test_tool_plan_validation.py -v
  cd agent-core && PYTHONPATH=src python -m unittest tests.test_tool_plan_validation -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import agent_core_api as m  # noqa: E402


class TestToolPlanValidation(unittest.TestCase):
    def test_sanitize_tool_path_dot_with_human_note(self):
        self.assertEqual(m._sanitize_tool_path(". (raíz del proyecto)"), ".")
        self.assertEqual(m._sanitize_tool_path("  . # comentario"), ".")

    def test_do_list_dir_dot_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            import os

            os.environ["ADA_WORKSPACE"] = td
            os.environ.pop("ADA_PROJECTS_ROOT", None)
            Path(td, "probe.txt").write_text("ok", encoding="utf-8")
            ok, out = m._do_list_dir(".")
            self.assertTrue(ok, out)
            self.assertIn("probe.txt", out)

    def test_extract_signals_pseudo_tools_mixed_with_list_dir(self):
        raw = "LIST_DIR: .\nCREATE_PAGE: landing\n"
        actions, _text_out, sig = m._extract_planned_actions(raw)
        self.assertTrue(sig["has_pseudo_tools"])
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "LIST_DIR")
        self.assertEqual(actions[0]["path"], ".")

    def test_extract_signals_meta_instruction(self):
        raw = "LIST_DIR: .\nEscribe WRITE_FILE con el HTML.\n"
        _a, _t, sig = m._extract_planned_actions(raw)
        self.assertTrue(sig["has_meta_instruction_lines"])

    def test_extract_signals_fence(self):
        raw = "```\nWRITE_FILE: x\na\nEND_FILE\n```\n"
        _a, _t, sig = m._extract_planned_actions(raw)
        self.assertTrue(sig["has_invalid_tool_syntax"])

    def test_extract_clean_minimal_plan(self):
        raw = """RUN_COMMAND: mkdir -p dockers/ada-landing-demo
WRITE_FILE: dockers/ada-landing-demo/index.html
<h1>ADA</h1>
END_FILE
"""
        actions, _t, sig = m._extract_planned_actions(raw)
        self.assertFalse(any(sig.values()), sig)
        self.assertEqual(len(actions), 2)

    def test_asset_consistency_missing_assets_is_rejected(self):
        raw = """WRITE_FILE: dockers/ada-landing-demo/index.html
<html>
  <head>
    <link rel="stylesheet" href="styles.css">
  </head>
  <body>
    <script src="app.js"></script>
  </body>
</html>
END_FILE
"""
        actions, _t, sig = m._extract_planned_actions(raw)
        self.assertFalse(sig["has_pseudo_tools"])
        self.assertFalse(sig["has_meta_instruction_lines"])
        # No hay styles.css/app.js en el plan: debe fallar consistencia.
        self.assertFalse(m._validate_artifact_asset_consistency(actions))

    def test_asset_consistency_ok_when_assets_written(self):
        raw = """WRITE_FILE: dockers/ada-landing-demo/index.html
<html>
  <head>
    <link rel="stylesheet" href="styles.css">
  </head>
  <body>
    <script src="app.js"></script>
  </body>
</html>
END_FILE
WRITE_FILE: dockers/ada-landing-demo/styles.css
body { margin: 0; }
END_FILE
WRITE_FILE: dockers/ada-landing-demo/app.js
console.log("ADA");
END_FILE
"""
        actions, _t, sig = m._extract_planned_actions(raw)
        self.assertFalse(any(sig.values()), sig)
        self.assertTrue(m._validate_artifact_asset_consistency(actions))

    def test_asset_consistency_reverse_styles_link_required(self):
        raw = """WRITE_FILE: dockers/ada-landing-demo/index.html
<html><head></head><body><h1>ADA</h1></body></html>
END_FILE
WRITE_FILE: dockers/ada-landing-demo/styles.css
body { margin: 0; }
END_FILE
"""
        actions, _t, _sig = m._extract_planned_actions(raw)
        # styles.css existe pero index.html no lo enlaza.
        self.assertFalse(m._validate_artifact_asset_consistency(actions))

    def test_inline_write_file_is_invalid_syntax(self):
        raw = 'WRITE_FILE: dockers/ada-landing-demo/index.html <h1>ADA</h1> END_FILE\n'
        _actions, _t, sig = m._extract_planned_actions(raw)
        self.assertTrue(sig["has_invalid_tool_syntax"])

if __name__ == "__main__":
    unittest.main()
