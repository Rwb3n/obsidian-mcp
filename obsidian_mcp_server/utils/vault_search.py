import os
import logging
import yaml # Needed for metadata search
from obsidian_mcp_server.config import settings
from obsidian_mcp_server.utils.exceptions import VaultError # Only need base VaultError here
from obsidian_mcp_server.utils.frontmatter import split_frontmatter
from obsidian_mcp_server.utils.paths import iter_vault_notes, vault_root

logger = logging.getLogger(__name__)

def search_notes_content(query):
    """Searches the content of all markdown notes for a query string.

    Args:
        query: The string to search for (case-insensitive).

    Returns:
        A list of relative note paths containing the query.
    """
    matches = []
    query_lower = query.lower()
    try:
        for relative_path, full_path in iter_vault_notes():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if query_lower in content.lower():
                    matches.append(relative_path)
            except Exception as e:
                # Log non-critical read errors during search, but continue
                logger.warning(f"[Search] Error reading {relative_path}: {e}")
                continue

        return matches

    except Exception as e:
        # Raise error only if the walk itself fails
        raise VaultError(f"Error during content search walk for query '{query}': {e}") from e

def search_notes_metadata(query):
    """Searches the metadata (YAML frontmatter) of all notes for a query string.

    Args:
        query: The string to search for in metadata values (case-insensitive).

    Returns:
        A list of relative note paths where the query was found in metadata values.
    """
    matches = []
    query_lower = query.lower()
    try:
        for relative_path, full_path in iter_vault_notes():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e_read:
                logger.warning(f"[MetaSearch] Error reading {relative_path}: {e_read}")
                continue

            try:
                metadata, _, _ = split_frontmatter(content)
            except yaml.YAMLError:
                # Ignore notes with invalid YAML for this search
                continue
            # Recursively check values in the metadata dict/list structure
            if metadata and _check_metadata_values(metadata, query_lower):
                matches.append(relative_path)

        return matches

    except Exception as e_walk:
        raise VaultError(f"Error during metadata search walk for query '{query}': {e_walk}") from e_walk

def _check_metadata_values(metadata_item, query_lower):
    """Helper to recursively search for a query in metadata values."""
    if isinstance(metadata_item, dict):
        for key, value in metadata_item.items():
            if _check_metadata_values(value, query_lower):
                return True
    elif isinstance(metadata_item, list):
        for item in metadata_item:
            if _check_metadata_values(item, query_lower):
                return True
    elif isinstance(metadata_item, str):
        if query_lower in metadata_item.lower():
            return True
    # Add checks for other types like int/float if needed, converting to str
    elif isinstance(metadata_item, (int, float, bool)):
        if query_lower in str(metadata_item).lower():
            return True
    return False

def search_folders(query):
    """Searches for folders whose names contain the query string.

    Args:
        query: The string to search for in folder names (case-insensitive).

    Returns:
        A list of relative folder paths matching the query.
    """
    matches = []
    query_lower = query.lower()
    try:
        vault = vault_root()
        for root, dirs, files in os.walk(vault):
            # Modify dirs in place to control the walk
            # Skip hidden directories and the backup directory
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != settings.backup_dir_name]

            for dirname in dirs:
                if query_lower in dirname.lower():
                    full_path = os.path.join(root, dirname)
                    relative_path = os.path.relpath(full_path, vault).replace('\\', '/')
                    matches.append(relative_path)

        # We only need to check the directories found during the walk
        return matches

    except Exception as e:
        raise VaultError(f"Error during folder search walk for query '{query}': {e}") from e


# --- Add other search functions below ---
