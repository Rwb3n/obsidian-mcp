import os
import subprocess
import sys


def _load_vault_path(env):
    code = "from obsidian_mcp_server.config import settings; print(settings.obsidian_vault_path)"
    clean = {k: v for k, v in os.environ.items() if not k.startswith("OMCP_")}
    return subprocess.run([sys.executable, "-c", code], env={**clean, **env}, capture_output=True, text=True)


def test_documented_env_var_is_used(tmp_path):
    result = _load_vault_path({"OMCP_VAULT_PATH": str(tmp_path)})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == os.path.realpath(tmp_path)


def test_field_name_env_var_still_accepted(tmp_path):
    result = _load_vault_path({"OMCP_OBSIDIAN_VAULT_PATH": str(tmp_path)})
    assert result.stdout.strip() == os.path.realpath(tmp_path)


def test_missing_vault_path_fails_loudly(tmp_path):
    result = subprocess.run(
        [sys.executable, "-c", "import obsidian_mcp_server.config"],
        env={k: v for k, v in os.environ.items() if not k.startswith("OMCP_")},
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert result.returncode != 0
    assert "obsidian_vault_path" in result.stderr.lower() or "omcp_vault_path" in result.stderr.lower()


def test_template_env_var(tmp_path):
    code = "from obsidian_mcp_server.config import settings; print(settings.daily_note_template_path)"
    clean = {k: v for k, v in os.environ.items() if not k.startswith("OMCP_")}
    env = {**clean, "OMCP_VAULT_PATH": str(tmp_path), "OMCP_DAILY_NOTE_TEMPLATE": "Templates/Daily.md"}
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert result.stdout.strip() == "Templates/Daily.md"
