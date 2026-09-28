import os

import pytest

from obsidian_mcp_server.utils import vault_reader, vault_writer, vault_search
from obsidian_mcp_server.utils.exceptions import InvalidPathError


@pytest.fixture
def sibling(vault):
    # A directory whose name shares the vault's prefix: "<vault>-evil"
    evil = vault.parent / (vault.name + "-evil")
    evil.mkdir()
    (evil / "secret.md").write_text("secret")
    return evil


def test_sibling_prefix_directory_is_rejected(vault, sibling):
    with pytest.raises(InvalidPathError):
        vault_reader.get_note_content(f"../{sibling.name}/secret.md")


def test_absolute_path_is_rejected(vault, sibling):
    with pytest.raises(InvalidPathError):
        vault_reader.get_note_content(str(sibling / "secret.md"))


def test_symlink_escaping_vault_is_rejected(vault, sibling):
    os.symlink(sibling, vault / "link")
    with pytest.raises(InvalidPathError):
        vault_reader.get_note_content("link/secret.md")
    with pytest.raises(InvalidPathError):
        vault_writer.edit_note("link/secret.md", "pwned")
    assert (sibling / "secret.md").read_text() == "secret"


def test_symlinked_note_outside_vault_is_skipped_by_search(vault, sibling):
    os.symlink(sibling / "secret.md", vault / "leak.md")
    assert vault_search.search_notes_content("secret") == []


def test_symlink_inside_vault_is_allowed(vault):
    (vault / "real").mkdir()
    (vault / "real" / "n.md").write_text("hi")
    os.symlink(vault / "real", vault / "alias")
    assert vault_reader.get_note_content("alias/n.md") == "hi"


@pytest.mark.parametrize("path", ["plugin.js", "notes/data.json", "n.md.js"])
def test_writes_require_markdown(vault, path):
    with pytest.raises(InvalidPathError):
        vault_writer.create_note(path, "x")
    assert not (vault / path).exists()


@pytest.mark.parametrize("path", [
    ".obsidian/plugins/evil/main.md",
    ".obsidian/community-plugins.md",
    "sub/.git/x.md",
    "_mcp_backups/x.md",
])
def test_hidden_and_backup_paths_rejected(vault, path):
    with pytest.raises(InvalidPathError):
        vault_writer.create_note(path, "x")
    with pytest.raises(InvalidPathError):
        vault_reader.get_note_content(path)


def test_obsidian_config_not_readable_or_editable(vault):
    (vault / ".obsidian").mkdir()
    (vault / ".obsidian" / "community-plugins.json").write_text("[]")
    with pytest.raises(InvalidPathError):
        vault_reader.get_note_content(".obsidian/community-plugins.json")
    with pytest.raises(InvalidPathError):
        vault_writer.edit_note(".obsidian/community-plugins.json", '["evil"]')
    assert (vault / ".obsidian" / "community-plugins.json").read_text() == "[]"


def test_hidden_folders_not_listed(vault):
    (vault / ".obsidian").mkdir()
    (vault / "_mcp_backups").mkdir()
    (vault / "Notes").mkdir()
    assert vault_reader.list_folders() == ["Notes"]


def test_normal_note_roundtrip(vault):
    assert vault_writer.create_note("Folder/New.md", "body", metadata={"b": 1, "a": 2})
    assert vault_reader.get_note_content("Folder/New.md") == "---\nb: 1\na: 2\n---\n\nbody"
    assert vault_writer.append_to_note("Folder/New.md", "more")
    assert vault_writer.delete_note("Folder/New.md")
    assert not (vault / "Folder" / "New.md").exists()
    assert any((vault / "_mcp_backups" / "Folder").iterdir())
