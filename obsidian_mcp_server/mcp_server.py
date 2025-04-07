import datetime
from typing import Any, Dict, Optional, List
import json # Import json

# Import the high-level server interface
from mcp.server.fastmcp import FastMCP, Context # Assuming Context might be needed later

# Import utility functions
# Use absolute import based on package structure
from obsidian_mcp_server.utils import vault_reader, vault_writer, vault_search, daily_notes

# Import our custom exceptions
from obsidian_mcp_server.utils.exceptions import VaultError, NoteNotFoundError, InvalidPathError, MetadataError, BackupError, NoteCreationError

# Import our central config
from obsidian_mcp_server.config import settings

# --- Instantiate FastMCP Server ---
# Give it a name relevant to its function
# Pass host and port from our config to FastMCP settings
mcp_app = FastMCP(
    "Obsidian Vault Access", 
    host=settings.server_host, 
    port=settings.server_port
)

# --- Define MCP Resources (Read-only operations IDENTIFIED BY URI) ---

# (No resources defined for now, as all require parameters)

# --- Define MCP Tools (Actions / Reads requiring parameters) ---

# Changed from resource to tool
@mcp_app.tool()
def search_notes_content(query: str) -> List[str]:
    """MCP Tool: Searches the content of all notes for a query string."""
    try:
        return vault_search.search_notes_content(query)
    except VaultError as e:
        # TODO: Map to specific MCP error (e.g., Internal Server Error)
        print(f"Error in search_notes_content tool: {e}")
        raise # Let FastMCP handle for now

# Changed from resource to tool
@mcp_app.tool()
def search_notes_metadata(query: str) -> List[str]:
    """MCP Tool: Searches the metadata of all notes for a query string."""
    try:
        return vault_search.search_notes_metadata(query)
    except VaultError as e:
        print(f"Error in search_notes_metadata tool: {e}")
        raise

# Changed from resource to tool
@mcp_app.tool()
def search_folders(query: str) -> List[str]:
    """MCP Tool: Searches for folders whose names contain the query string."""
    try:
        return vault_search.search_folders(query)
    except VaultError as e:
        print(f"Error in search_folders tool: {e}")
        raise

# Changed from resource to tool
@mcp_app.tool()
def get_daily_note_path(target_date_iso: Optional[str] = None) -> str:
    """MCP Tool: Calculates the path for a daily note. Raises error if path invalid."""
    target_dt = None
    if target_date_iso:
        try:
            target_dt = datetime.date.fromisoformat(target_date_iso)
        except ValueError:
            # Let FastMCP handle this via VaultError
            raise VaultError(f"Invalid date format: {target_date_iso}. Use YYYY-MM-DD.")
    try:
        path = daily_notes.get_daily_note_path(target_dt)
        # get_daily_note_path now raises error instead of returning None
        return path
    except (VaultError, InvalidPathError) as e:
        print(f"Error in get_daily_note_path tool: {e}")
        raise


# --- Tools (Previously Resources, now Tools) ---

# Changed from resource to tool
@mcp_app.tool()
def list_folders(relative_path: str = ".") -> List[str]:
    """MCP Tool: Lists subfolders within a given relative path."""
    try:
        # list_folders now raises error instead of returning None
        return vault_reader.list_folders(relative_path)
    except (VaultError, InvalidPathError) as e:
        print(f"Error in list_folders tool: {e}")
        raise # Let FastMCP handle exceptions

@mcp_app.tool()
def list_notes(relative_path: str = ".") -> List[str]:
    """MCP Tool: Lists markdown notes within a given relative path."""
    try:
        # list_notes now raises error instead of returning None
        return vault_reader.list_notes(relative_path)
    except (VaultError, InvalidPathError) as e:
        print(f"Error in list_notes tool: {e}")
        raise

@mcp_app.tool()
def get_note_content(note_path: str) -> str:
    """MCP Tool: Reads the full content of a specific note file."""
    try:
        # get_note_content now raises error instead of returning None
        return vault_reader.get_note_content(note_path)
    except (VaultError, InvalidPathError, NoteNotFoundError) as e:
        print(f"Error in get_note_content tool: {e}")
        raise

@mcp_app.tool()
def get_note_metadata(note_path: str) -> Dict[str, Any]:
    """MCP Tool: Reads the YAML frontmatter metadata from a note file."""
    try:
        # get_note_metadata returns {} on parse error, raises on read error
        return vault_reader.get_note_metadata(note_path)
    except (VaultError, InvalidPathError, NoteNotFoundError, MetadataError) as e:
        print(f"Error in get_note_metadata tool: {e}")
        raise

@mcp_app.tool()
def get_outgoing_links(note_path: str) -> List[str]:
    """MCP Tool: Finds all outgoing Obsidian links [[...]] in a note."""
    try:
        return vault_reader.get_outgoing_links(note_path)
    except (VaultError, InvalidPathError, NoteNotFoundError) as e:
        print(f"Error in get_outgoing_links tool: {e}")
        raise

@mcp_app.tool()
def get_backlinks(note_path: str) -> str:
    """MCP Tool: Finds all notes linking to the target note_path. Returns a JSON list of paths."""
    try:
        backlink_list = vault_reader.get_backlinks(note_path)
        return json.dumps(backlink_list) # Return as JSON string
    except (NoteNotFoundError, InvalidPathError, VaultError) as e:
        print(f"Error in get_backlinks tool: {e}")
        raise # Propagate known errors
    except Exception as e:
        print(f"Unexpected error in get_backlinks tool: {e}")
        raise VaultError(f"Unexpected error finding backlinks for {note_path}: {e}") from e

@mcp_app.tool()
def get_all_tags() -> str: # Return type is now a JSON string
    """MCP Tool: Scans the entire vault for tags (frontmatter and inline) and returns a unique list as a JSON string."""
    try:
        tag_list = vault_reader.get_all_tags()
        return json.dumps(tag_list) # Explicitly dump list to JSON string
    except VaultError as e: # Catch potential general VaultErrors from os.walk etc.
        print(f"Error in get_all_tags tool: {e}")
        raise

# --- Writer Tools (Already tools, unchanged) ---

@mcp_app.tool()
def create_note(relative_note_path: str, content: str = "", metadata: Optional[Dict[str, Any]] = None) -> bool:
    """MCP Tool: Creates a new note file with optional YAML frontmatter."""
    return vault_writer.create_note(relative_note_path, content, metadata=metadata)

@mcp_app.tool()
def edit_note(relative_note_path: str, new_content: str, backup: bool = True) -> bool:
    """MCP Tool: Overwrites an existing note with new content, with backup option."""
    return vault_writer.edit_note(relative_note_path, new_content, backup)

@mcp_app.tool()
def append_to_note(relative_note_path: str, content: str, backup: bool = True) -> bool:
    """MCP Tool: Appends content to the end of an existing note, with backup option."""
    return vault_writer.append_to_note(relative_note_path, content, backup)

@mcp_app.tool()
def update_note_metadata(relative_note_path: str, metadata_updates: Dict[str, Any], backup: bool = True) -> bool:
    """MCP Tool: Updates the YAML frontmatter of an existing note, with backup option."""
    # Return the boolean or raise the VaultError
    result = vault_writer.update_metadata(relative_note_path, metadata_updates, backup)
    if isinstance(result, VaultError):
        raise result # Let FastMCP handle the error
    return result # Return the boolean

@mcp_app.tool()
def delete_note(relative_note_path: str, backup: bool = True) -> bool:
    """MCP Tool: Deletes a note file, optionally creating a backup first."""
    try:
        # vault_writer.delete_note raises exceptions on failure
        return vault_writer.delete_note(relative_note_path, backup)
    except (NoteNotFoundError, InvalidPathError, BackupError, VaultError) as e:
        print(f"Error in delete_note tool: {e}")
        raise # Let FastMCP handle the error propagation

@mcp_app.tool()
def create_daily_note(target_date_iso: Optional[str] = None, force_create: bool = False) -> Optional[str]:
    """MCP Tool: Creates a daily note (date optional, defaults today). Returns path or None."""
    target_dt = None
    if target_date_iso:
        try:
            target_dt = datetime.date.fromisoformat(target_date_iso)
        except ValueError:
            print(f"Error: Invalid date format: {target_date_iso}. Use YYYY-MM-DD.")
            return None # Or raise?
    return daily_notes.create_daily_note(target_dt, force_create)

@mcp_app.tool()
def append_to_daily_note(content_to_append: str, target_date_iso: Optional[str] = None, backup: bool = True) -> bool:
    """MCP Tool: Appends content to a daily note (date optional, defaults today)."""
    target_dt = None
    if target_date_iso:
        try:
            target_dt = datetime.date.fromisoformat(target_date_iso)
        except ValueError:
            print(f"Error: Invalid date format: {target_date_iso}. Use YYYY-MM-DD.")
            return False # Or raise?
    return daily_notes.append_to_daily_note(content_to_append, target_dt, backup)

# Note: The old handle_mcp_request and ACTION_MAP are removed. 