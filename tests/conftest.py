import os
import tempfile

import pytest

# Settings are loaded at import time and require a vault; point them at a placeholder
# before any package module is imported. Each test then gets its own vault.
os.environ.setdefault("OMCP_VAULT_PATH", tempfile.mkdtemp(prefix="omcp-placeholder-"))

from obsidian_mcp_server.config import settings  # noqa: E402


@pytest.fixture
def vault(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    root.mkdir()
    monkeypatch.setattr(settings, "obsidian_vault_path", os.path.realpath(root))
    return root
