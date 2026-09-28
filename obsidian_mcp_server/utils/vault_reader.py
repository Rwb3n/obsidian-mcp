import os
import yaml # Added for metadata parsing
import re # Added for link/tag parsing
import logging
# Import config and exceptions
from obsidian_mcp_server.config import settings
from obsidian_mcp_server.utils.exceptions import VaultError, NoteNotFoundError, InvalidPathError, MetadataError
from obsidian_mcp_server.utils.frontmatter import split_frontmatter
from obsidian_mcp_server.utils.paths import resolve_vault_path, iter_vault_notes

logger = logging.getLogger(__name__)

def list_folders(relative_path="."):
    """Lists subfolders within a given relative path inside the vault.

    Args:
        relative_path: The path relative to the vault root. Defaults to root.

    Returns:
        A list of folder names (hidden and backup folders excluded).
    """
    base_path = resolve_vault_path(relative_path)
    if not os.path.isdir(base_path):
        raise InvalidPathError(f"Directory not found or invalid: {relative_path}")

    try:
        return [
            d for d in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, d))
            and not d.startswith('.') and d != settings.backup_dir_name
        ]
    except Exception as e:
        raise VaultError(f"Error listing folders in {relative_path}: {e}") from e


def list_notes(relative_path="."):
    """Lists markdown notes within a given relative path inside the vault.

    Args:
        relative_path: The path relative to the vault root. Defaults to root.

    Returns:
        A list of note filenames (including .md extension).
    """
    base_path = resolve_vault_path(relative_path)
    if not os.path.isdir(base_path):
        raise InvalidPathError(f"Directory not found or invalid: {relative_path}")

    try:
        notes = [f for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f)) and f.lower().endswith('.md')]
        return notes
    except Exception as e:
        raise VaultError(f"Error listing notes in {relative_path}: {e}") from e


def get_note_content(note_path):
    """Reads the full content of a specific note file.

    Args:
        note_path: The path to the note file, relative to the vault root.
                   Should include the .md extension.

    Returns:
        The content of the note as a string.
    """
    full_path = resolve_vault_path(note_path)

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        raise NoteNotFoundError(f"Note not found: {note_path}") from None
    except Exception as e:
        raise VaultError(f"Error reading note {note_path}: {e}") from e

def get_note_metadata(note_path):
    """Reads the YAML frontmatter metadata from a note file.

    Args:
        note_path: The path to the note file, relative to the vault root.

    Returns:
        A dictionary representing the YAML metadata, or an empty dict
        if no frontmatter exists or it cannot be parsed.
    """
    content = get_note_content(note_path)
    try:
        metadata, _, _ = split_frontmatter(content)
    except yaml.YAMLError as e:
        # Log warning but don't raise - treat as note with no valid metadata
        logger.warning(f"[Meta] Could not parse YAML in {note_path}: {e}")
        return {}
    except Exception as e:
        raise MetadataError(f"Unexpected error parsing YAML in {note_path}: {e}") from e
    return metadata or {}

def get_outgoing_links(note_path):
    """Finds all outgoing Obsidian links [[...]] in a note.

    Args:
        note_path: The path to the note file, relative to the vault root.

    Returns:
        A list of linked note names (without the brackets).
    """
    try:
        content = get_note_content(note_path) # Reuse existing logic (will raise if not found)
        return _find_links(content)
    except (NoteNotFoundError, InvalidPathError): # Propagate these errors
        raise
    except Exception as e:
        raise VaultError(f"Error parsing links in {note_path}: {e}") from e

def _find_links(content):
    return re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)

# --- Add other reader functions below ---

def get_all_tags() -> list[str]:
    """Scans the entire vault and returns a sorted list of unique tags.

    Finds tags in YAML frontmatter (under 'tags' key, handles strings/lists)
    and inline tags in the note body (e.g., #tag, #nested/tag).

    Returns:
        A sorted list of unique tag strings found in the vault.
    """
    all_tags = set()

    # Regex for inline tags: starts with #, followed by non-whitespace/non-#,
    # potentially including / for nested tags.
    # Avoids matching headers like ### Title or mid-word #.
    # Matches: #tag, #nested/tag, #tag1/tag2
    # Doesn't match: ## Header, word#tag, # (just hash)
    inline_tag_regex = re.compile(r"(?:^|\s)#([\w-]+(?:/[\w-]+)*)")

    for relative_path, full_path in iter_vault_notes():
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                metadata, _, body_content = split_frontmatter(content)
            except yaml.YAMLError as e:
                logger.warning(f"[Tags] Could not parse YAML in {relative_path}: {e}")
                metadata, body_content = None, content

            if metadata and 'tags' in metadata:
                tags_meta = metadata['tags']
                if isinstance(tags_meta, list):
                    for tag in tags_meta:
                        if isinstance(tag, str):
                            all_tags.add(tag.strip())
                elif isinstance(tags_meta, str):
                    # Handle comma or space separated tags in a single string
                    for tag_part in re.split(r'[\s,]+', tags_meta):
                        if tag_part:
                            all_tags.add(tag_part.strip())

            # Find inline tags in the body
            for match in inline_tag_regex.finditer(body_content):
                all_tags.add(match.group(1))

        except Exception as e:
            logger.warning(f"[Tags] Skipping note due to error: {relative_path} - {e}")

    return sorted(list(all_tags))

def get_backlinks(target_note_path: str) -> list[str]:
    """Finds all notes in the vault that link to the target note.

    Args:
        target_note_path: The relative path of the note whose backlinks are sought.

    Returns:
        A list of relative paths of notes that link to the target note.
    """
    backlinks = []
    # Normalize the target path for comparison
    normalized_target = target_note_path.replace('\\', '/').lower()
    # Also consider target without extension for links like [[My Note]]
    target_no_ext, _ = os.path.splitext(normalized_target)

    # 1. Check if the target note itself exists
    target_full_path = resolve_vault_path(target_note_path)
    if not os.path.isfile(target_full_path):
        raise NoteNotFoundError(f"[Backlinks] Target note not found: {target_note_path}")

    # 2. Walk through the vault
    for linking_note_rel_path, full_path in iter_vault_notes():
        # Don't check the target note itself
        if linking_note_rel_path.lower() == normalized_target:
            continue

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                outgoing_links = _find_links(f.read())

            # Check if any outgoing link matches the target (with or without extension)
            for link in outgoing_links:
                normalized_link = link.replace('\\', '/').lower()
                link_no_ext, _ = os.path.splitext(normalized_link)

                # Match if link equals target (with/without ext) or link (without ext) equals target (without ext)
                if normalized_link == normalized_target or link_no_ext == target_no_ext:
                    backlinks.append(linking_note_rel_path)
                    break # Found a link, no need to check further links in this file

        except Exception as e:
            logger.warning(f"[Backlinks] Skipping note due to error reading links: {linking_note_rel_path} - {e}")

    return sorted(list(set(backlinks))) # Return unique, sorted list
