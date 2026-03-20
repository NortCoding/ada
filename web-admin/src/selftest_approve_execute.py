import importlib
import os
import tempfile

from fastapi.testclient import TestClient


def _load_app(*, files_root: str, enable_fs: bool, allowlist: str = "ls,python3"):
    os.environ["ADA_FILES_ROOT"] = files_root
    os.environ["ENABLE_AGENT_FS"] = "1" if enable_fs else "0"
    os.environ["ADA_UI_RUN_ALLOWLIST"] = allowlist
    os.environ["ADA_UI_RUN_TIMEOUT"] = "10"

    mod = importlib.import_module("web_admin_api")
    importlib.reload(mod)
    return mod.app


def _post(client: TestClient, action_type: str, payload: dict):
    return client.post("/api/approve/execute", json={"action_type": action_type, "payload": payload})


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        # 1) create_file success
        app = _load_app(files_root=tmp, enable_fs=True, allowlist="ls,python3")
        client = TestClient(app)
        r = _post(client, "create_file", {"path": "x/a.txt", "content": "hola\n"})
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["success"] is True
        assert j["verification"]["sha256_after"]

        # 2) run_command allowed
        r = _post(client, "run_command", {"command": "ls"})
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["action_type"] == "run_command"
        assert "exit_code" in j["verification"]

        # 3) run_command blocked
        r = _post(client, "run_command", {"command": "rm -rf /"})
        assert r.status_code == 403, r.text
        j = r.json()
        assert "detail" in j and isinstance(j["detail"], dict)
        assert j["detail"]["error"] == "Command not allowed"

        # 4) apply_patch success
        r = _post(client, "apply_patch", {"path": "x/a.txt", "new_content": "adios\n"})
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["verification"]["changed"] is True

        # 5) filesystem disabled rejection
        app2 = _load_app(files_root=tmp, enable_fs=False, allowlist="ls,python3")
        client2 = TestClient(app2)
        r = _post(client2, "create_file", {"path": "y/b.txt", "content": "nope\n"})
        assert r.status_code == 403, r.text
        j = r.json()
        assert j["detail"]["error"] == "Filesystem write disabled"

    print("selftest_approve_execute: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

