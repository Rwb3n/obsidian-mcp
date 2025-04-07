import os
import yaml # Added for metadata parsing
import re # Added for link/tag parsing
# Import config and exceptions
from obsidian_mcp_server.config import settings
from obsidian_mcp_server.utils.exceptions import VaultError, NoteNotFoundError, InvalidPathError, MetadataError

# Use vault path from settings
VAULT_PATH = settings.obsidian_vault_path

def list_folders(relative_path="."):
    """Lists subfolders within a given relative path inside the vault.

    Args:
        relative_path: The path relative to the vault root. Defaults to root.

    Returns:
        A list of folder names. Returns None if the path is invalid.
    """
    base_path = os.path.join(VAULT_PATH, relative_path)
    # Security check (ensure it's within VAULT_PATH after joining)
    if not os.path.abspath(base_path).startswith(os.path.abspath(VAULT_PATH)):
        raise InvalidPathError(f"Attempted access outside vault: {relative_path}")
    if not os.path.isdir(base_path):
        raise InvalidPathError(f"Directory not found or invalid: {relative_path}")

    try:
        folders = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        return folders
    except Exception as e:
        raise VaultError(f"Error listing folders in {relative_path}: {e}") from e


def list_notes(relative_path="."):
    """Lists markdown notes within a given relative path inside the vault.

    Args:
        relative_path: The path relative to the vault root. Defaults to root.

    Returns:
        A list of note filenames (including .md extension). Returns None if path invalid.
    """
    base_path = os.path.join(VAULT_PATH, relative_path)
    if not os.path.abspath(base_path).startswith(os.path.abspath(VAULT_PATH)):
        raise InvalidPathError(f"Attempted access outside vault: {relative_path}")
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
        The content of the note as a string, or None if the file
        cannot be found or read.
    """
    full_path = os.path.join(VAULT_PATH, note_path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(VAULT_PATH)):
        raise InvalidPathError(f"Attempted access outside vault: {note_path}")

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
        if no frontmatter exists or there's an error.
    """
    full_path = os.path.join(VAULT_PATH, note_path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(VAULT_PATH)):
        raise InvalidPathError(f"Attempted access outside vault: {note_path}")

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        raise NoteNotFoundError(f"Note not found: {note_path}") from None
    except Exception as e:
        raise VaultError(f"Error reading note {note_path} for metadata: {e}") from e

    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {} # Malformed frontmatter - return empty, don't raise

    frontmatter_yaml = parts[1]
    try:
        metadata = yaml.safe_load(frontmatter_yaml)
        return metadata if isinstance(metadata, dict) else {}
    except yaml.YAMLError as e:
        # Log warning but don't raise - treat as note with no valid metadata
        print(f"Warning [Meta]: Could not parse YAML in {note_path}: {e}")
        return {}
    except Exception as e:
        raise MetadataError(f"Unexpected error parsing YAML in {note_path}: {e}") from e

def get_outgoing_links(note_path):
    """Finds all outgoing Obsidian links [[...]] in a note.

    Args:
        note_path: The path to the note file, relative to the vault root.

    Returns:
        A list of linked note names (without the brackets). Returns
        an empty list if no links are found or in case of error.
    """
    try:
        content = get_note_content(note_path) # Reuse existing logic (will raise if not found)
        links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
        return links
    except NoteNotFoundError: # Propagate this error
        raise
    except InvalidPathError: # Propagate this error
        raise
    except Exception as e:
        raise VaultError(f"Error parsing links in {note_path}: {e}") from e

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

    for root, _, files in os.walk(VAULT_PATH):
        # Skip backup directory
        if os.path.basename(root) == settings.backup_dir_name:
             continue
        # Skip directories starting with '.' (like .obsidian)
        if os.path.basename(root).startswith('.'):
             continue
             
        for filename in files:
            if filename.lower().endswith('.md'):
                relative_path = os.path.relpath(os.path.join(root, filename), VAULT_PATH)
                relative_path = relative_path.replace('\\', '/') # Normalize path
                
                try:
                    # Get metadata
                    metadata = get_note_metadata(relative_path)
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
                                     
                    # Get body content (reuse get_note_content)
                    # Only read content if needed for inline tags
                    content = get_note_content(relative_path)
                    
                    # Extract body if frontmatter exists
                    body_content = content
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                             body_content = parts[2]
                             
                    # Find inline tags in the body
                    for match in inline_tag_regex.finditer(body_content):
                        all_tags.add(match.group(1))
                        
                except (NoteNotFoundError, InvalidPathError, MetadataError, VaultError) as e:
                    print(f"Warning [Tags]: Skipping note due to error: {relative_path} - {e}")
                except Exception as e:
                    print(f"Warning [Tags]: Unexpected error processing note {relative_path}: {e}")

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
    
    # 1. Check if the target note itself exists (optional, but good practice)
    target_full_path = os.path.join(VAULT_PATH, target_note_path)
    if not os.path.abspath(target_full_path).startswith(os.path.abspath(VAULT_PATH)):
        raise InvalidPathError(f"[Backlinks] Target path outside vault: {target_note_path}")
    if not os.path.isfile(target_full_path):
        raise NoteNotFoundError(f"[Backlinks] Target note not found: {target_note_path}")

    # 2. Walk through the vault
    for root, _, files in os.walk(VAULT_PATH):
        # Skip backup directory and hidden dirs
        if os.path.basename(root) == settings.backup_dir_name or os.path.basename(root).startswith('.'):
            continue

        for filename in files:
            if filename.lower().endswith('.md'):
                linking_note_rel_path = os.path.relpath(os.path.join(root, filename), VAULT_PATH)
                linking_note_rel_path = linking_note_rel_path.replace('\\', '/') # Normalize

                # Don't check the target note itself
                if linking_note_rel_path.lower() == normalized_target:
                    continue
                
                try:
                    # Use get_outgoing_links which handles reading the file
                    outgoing_links = get_outgoing_links(linking_note_rel_path)
                    
                    # Check if any outgoing link matches the target (with or without extension)
                    for link in outgoing_links:
                        normalized_link = link.replace('\\', '/').lower()
                        link_no_ext, _ = os.path.splitext(normalized_link)
                        
                        # Match if link equals target (with/without ext) or link (without ext) equals target (without ext)
                        if normalized_link == normalized_target or link_no_ext == target_no_ext:
                            backlinks.append(linking_note_rel_path)
                            break # Found a link, no need to check further links in this file
                            
                except (NoteNotFoundError, InvalidPathError, VaultError) as e:
                    print(f"Warning [Backlinks]: Skipping note due to error reading links: {linking_note_rel_path} - {e}")
                except Exception as e:
                    print(f"Warning [Backlinks]: Unexpected error processing note {linking_note_rel_path}: {e}")

    return sorted(list(set(backlinks))) # Return unique, sorted list

# Example usage (for testing - can be removed later)
if __name__ == '__main__':
    print("Folders in Vault Root:", list_folders())
    print("Notes in Vault Root:", list_notes())

    # Example for a subfolder (replace 'YourSubfolder' if needed)
    # subfolder_path = "YourSubfolder"
    # print(f"Folders in {subfolder_path}:", list_folders(subfolder_path))
    # print(f"Notes in {subfolder_path}:", list_notes(subfolder_path))

    # Example for reading a note (replace 'YourNote.md' if needed)
    # note_to_read = "YourNote.md"
    # content = get_note_content(note_to_read)
    # if content:
    #     print(f"\nContent of {note_to_read}:\n{content[:200]}...") # Print first 200 chars
    # else:
    #     print(f"Could not read {note_to_read}")

    # Example for reading metadata (replace 'YourNoteWithMetadata.md' if needed)
    # note_with_meta = "YourNoteWithMetadata.md"
    # metadata = get_note_metadata(note_with_meta)
    # if metadata:
    #     print(f"\nMetadata for {note_with_meta}:\n{metadata}")
    # else:
    #     print(f"No metadata found or error for {note_with_meta}")

    # Example for reading links (replace 'YourNoteWithLinks.md' if needed)
    # note_with_links = "YourNoteWithLinks.md"
    # links = get_outgoing_links(note_with_links)
    # if links:
    #     print(f"\nOutgoing links in {note_with_links}:\n{links}")
    # else:
    #     print(f"No outgoing links found or error for {note_with_links}")
        
    # --- Test get_all_tags ---
    print("\nScanning for all tags in vault...")
    all_vault_tags = get_all_tags()
    print(f"Found {len(all_vault_tags)} unique tags:")
    # Print first 50 tags for brevity
    print(all_vault_tags[:50])
    
    # --- Test get_backlinks ---
    # Replace with a note in your vault that you know has backlinks
    test_backlink_target = "_MCP_Test_Client_Note.md" 
    # Create a temporary linking note for testing
    linking_note_path = "_MCP_Test_Backlink_Source.md"
    try:
        from obsidian_mcp_server.utils.vault_writer import create_note, delete_note
        # Ensure the target note exists for the test
        print(f"\nEnsuring target note '{test_backlink_target}' exists for backlink test...")
        create_note(test_backlink_target, content="# Target Note\nThis note is the target for backlinks.", metadata=None)
        
        print(f"Creating temporary note '{linking_note_path}' linking to '{test_backlink_target}'")
        create_note(linking_note_path, content=f"Link to [[{test_backlink_target}]] and [[{test_backlink_target}|Alias]]", metadata=None)
        
        print(f"Scanning for backlinks to {test_backlink_target}...")
        found_backlinks = get_backlinks(test_backlink_target)
        print(f"Found {len(found_backlinks)} backlinks:")
        print(found_backlinks)
        if linking_note_path in found_backlinks:
            print("  Verification PASSED: Test linking note found.")
        else:
            print("  Verification FAILED: Test linking note NOT found.")
        
        # Clean up the temporary linking note
        print(f"Cleaning up {linking_note_path}...")
        delete_note(linking_note_path, backup=False)
        # Clean up the temporary target note
        print(f"Cleaning up {test_backlink_target}...")
        delete_note(test_backlink_target, backup=False)
        print("Cleanup complete.")
        
    except ImportError:
        print("Skipping backlink test setup/cleanup (vault_writer not available)")
        # Attempt cleanup even on error
        try:
            if os.path.exists(os.path.join(VAULT_PATH, linking_note_path)):
                 delete_note(linking_note_path, backup=False)
                 print("Cleanup attempted for linking note after error.")
            if os.path.exists(os.path.join(VAULT_PATH, test_backlink_target)):
                 delete_note(test_backlink_target, backup=False)
                 print("Cleanup attempted for target note after error.")
        except Exception as cleanup_e:
            print(f"Error during cleanup after error: {cleanup_e}") 