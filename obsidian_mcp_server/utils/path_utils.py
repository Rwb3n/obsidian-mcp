"""Path containment helpers for safely confining file access to the vault."""

import os


def is_path_within_vault(candidate_path, vault_path):
    """Return True if ``candidate_path`` resolves to a location inside
    ``vault_path`` (the vault root itself counts as inside).

    This replaces the previous ``os.path.abspath(p).startswith(vault)`` check,
    which is vulnerable to a sibling-directory bypass: with a vault of
    ``/home/user/vault``, a prefix match wrongly accepts
    ``/home/user/vault-private/...`` because the string starts with the vault
    path. Using ``os.path.commonpath`` compares whole path components instead,
    so only genuine descendants of the vault are accepted.

    ``os.path.realpath`` is applied to both sides so that symlinks inside the
    join cannot be used to escape the vault either.
    """
    real_vault = os.path.realpath(vault_path)
    real_candidate = os.path.realpath(candidate_path)
    try:
        return os.path.commonpath([real_vault, real_candidate]) == real_vault
    except ValueError:
        # commonpath raises ValueError when the paths cannot be compared, e.g.
        # they live on different drives on Windows, or mix absolute/relative.
        # Any such case is, by definition, not inside the vault.
        return False
