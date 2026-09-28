"""Path resolution and containment checks for vault access."""

import os
from obsidian_mcp_server.config import settings
from obsidian_mcp_server.utils.exceptions import InvalidPathError

NOTE_EXTENSION = ".md"


def vault_root():
    """Returns the canonical (symlink-resolved) vault path."""
    return os.path.realpath(settings.obsidian_vault_path)


def is_within(path, root):
    """True if the canonical `path` is `root` or lies beneath it."""
    path = os.path.normcase(path)
    root = os.path.normcase(root)
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:  # Different drives on Windows
        return False


def _is_hidden_or_backup(relative_path):
    """True if any component is hidden (e.g. .obsidian, .trash) or the backup dir."""
    parts = [p for p in relative_path.replace("\\", "/").split("/") if p not in ("", ".")]
    return any(p.startswith(".") or p == settings.backup_dir_name for p in parts)


def resolve_vault_path(relative_path, *, require_note=False):
    """Resolves a vault-relative path to a canonical absolute path.

    Symlinks are resolved before the containment check, so a link pointing
    outside the vault is rejected. Hidden paths (.obsidian, .git, ...) and the
    backup directory are never exposed.

    Args:
        relative_path: Path relative to the vault root.
        require_note: If True, the path must end in '.md'.

    Raises:
        InvalidPathError: If the path escapes the vault, is hidden, or is not a note
            when one is required.
    """
    if relative_path is None or "\x00" in relative_path:
        raise InvalidPathError(f"Invalid path: {relative_path!r}")
    root = vault_root()
    if os.path.isabs(relative_path):
        raise InvalidPathError(f"Absolute paths are not allowed: {relative_path}")
    full_path = os.path.realpath(os.path.join(root, relative_path))
    if not is_within(full_path, root):
        raise InvalidPathError(f"Attempted access outside vault: {relative_path}")
    if _is_hidden_or_backup(os.path.relpath(full_path, root)):
        raise InvalidPathError(f"Access to hidden or backup paths is not allowed: {relative_path}")
    if require_note and not full_path.lower().endswith(NOTE_EXTENSION):
        raise InvalidPathError(f"Only '{NOTE_EXTENSION}' notes are allowed: {relative_path}")
    return full_path


def iter_vault_notes():
    """Yields (relative_path, full_path) for every note in the vault.

    Skips hidden directories, the backup directory, and symlinks resolving
    outside the vault.
    """
    root = vault_root()
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != settings.backup_dir_name]
        for filename in files:
            if not filename.lower().endswith(NOTE_EXTENSION):
                continue
            full_path = os.path.join(current, filename)
            if not is_within(os.path.realpath(full_path), root):
                continue
            relative_path = os.path.relpath(full_path, root).replace("\\", "/")
            yield relative_path, full_path
