import os
import yaml # Needed for metadata search
from obsidian_mcp_server.config import settings
from obsidian_mcp_server.utils.exceptions import VaultError # Only need base VaultError here

# Use config settings
VAULT_PATH = settings.obsidian_vault_path

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
        for root, dirs, files in os.walk(VAULT_PATH):
            # Optional: Skip hidden directories like .obsidian, .trash, .vault_backups
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for filename in files:
                if filename.lower().endswith('.md'):
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, VAULT_PATH).replace('\\', '/')

                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if query_lower in content.lower():
                            matches.append(relative_path)
                    except Exception as e:
                        # Log non-critical read errors during search, but continue
                        print(f"Warning [Search]: Error reading {relative_path}: {e}")
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
        for root, dirs, files in os.walk(VAULT_PATH):
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for filename in files:
                if filename.lower().endswith('.md'):
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, VAULT_PATH).replace('\\', '/')

                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        if not content.startswith("---"):
                            continue # No frontmatter

                        parts = content.split("---", 2)
                        if len(parts) < 3:
                            continue # Malformed frontmatter

                        frontmatter_yaml = parts[1]
                        try:
                            metadata = yaml.safe_load(frontmatter_yaml)
                            if isinstance(metadata, dict):
                                # Recursively check values in the metadata dict/list structure
                                if _check_metadata_values(metadata, query_lower):
                                     matches.append(relative_path)
                        except yaml.YAMLError:
                            # Ignore notes with invalid YAML for this search
                            continue
                        except Exception as e_parse:
                            print(f"Warning [MetaSearch]: Error parsing metadata for {relative_path}: {e_parse}")
                            continue

                    except Exception as e_read:
                        print(f"Warning [MetaSearch]: Error reading {relative_path}: {e_read}")
                        continue

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
        for root, dirs, files in os.walk(VAULT_PATH):
            # Modify dirs in place to control the walk
            # Keep only directories not starting with '.' for further traversal
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for dirname in dirs:
                if query_lower in dirname.lower():
                    full_path = os.path.join(root, dirname)
                    relative_path = os.path.relpath(full_path, VAULT_PATH).replace('\\', '/')
                    matches.append(relative_path)

        # We only need to check the directories found during the walk
        return matches

    except Exception as e:
        raise VaultError(f"Error during folder search walk for query '{query}': {e}") from e


# --- Add other search functions below ---

# Example usage (for testing)
if __name__ == '__main__':
    search_term = "test" # Replace with a term likely in your vault
    print(f"Searching for notes containing '{search_term}':")
    results = search_notes_content(search_term)
    if results:
        print("Found matches:")
        for note in results:
            print(f"  - {note}")
    else:
        print("No matching notes found.")

    meta_search_term = "draft" # Replace with a term likely in your metadata
    print(f"\nSearching for notes with metadata containing '{meta_search_term}':")
    meta_results = search_notes_metadata(meta_search_term)
    if meta_results:
        print("Found matches in metadata:")
        for note in meta_results:
            print(f"  - {note}")
    else:
        print("No matching notes found in metadata.")

    folder_search_term = "Folder" # Replace with part of a folder name in your vault
    print(f"\nSearching for folders containing '{folder_search_term}':")
    folder_results = search_folders(folder_search_term)
    if folder_results:
        print("Found matching folders:")
        for folder in folder_results:
            print(f"  - {folder}")
    else:
        print("No matching folders found.") 