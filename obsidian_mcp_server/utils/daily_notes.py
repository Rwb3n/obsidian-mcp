import os
import datetime
import re # Import regular expressions
import logging
# Import config, exceptions, and writers
from obsidian_mcp_server.config import settings
from obsidian_mcp_server.utils.vault_writer import create_note, append_to_note # VAULT_PATH no longer needed from here
from obsidian_mcp_server.utils.exceptions import VaultError, NoteNotFoundError, InvalidPathError, NoteCreationError, MetadataError, BackupError
from obsidian_mcp_server.utils.paths import resolve_vault_path

logger = logging.getLogger(__name__)

# Use config settings
DAILY_NOTE_LOCATION = settings.daily_note_location
DAILY_NOTE_FORMAT = settings.daily_note_format
DAILY_NOTE_TEMPLATE_PATH = settings.daily_note_template_path # Can be None

def get_daily_note_path(target_date=None):
    """Calculates the relative path for a daily note based on config.

    Args:
        target_date: A datetime.date object. Defaults to today if None.

    Returns:
        The relative path string (e.g., "2023-10-27.md" or "Daily/2023-10-27.md").
    """
    if target_date is None:
        target_date = datetime.date.today()

    try:
        # Format the filename
        filename = target_date.strftime(DAILY_NOTE_FORMAT) + ".md"

        # --- Handle location formatting ---
        location_template = DAILY_NOTE_LOCATION

        # Define a function to replace placeholders using regex
        def replace_date_placeholder(match):
            format_code = match.group(1) # Get the code inside {{date: ... }}
            # Map common placeholders to strftime codes
            strftime_map = {
                'YYYY': '%Y',
                'MM': '%m',
                'DD': '%d',
                'YY': '%y',
                'M': '%#m' if os.name != 'nt' else '%m', # Month without leading zero (platform dependent)
                'D': '%#d' if os.name != 'nt' else '%d', # Day without leading zero (platform dependent)
                # Add more mappings as needed
            }
            strftime_code = strftime_map.get(format_code)
            if strftime_code:
                try:
                    return target_date.strftime(strftime_code)
                except ValueError:
                    return match.group(0) # Return original if format invalid
            else:
                # If format code unknown, return the original placeholder
                logger.warning(f"Unknown daily note location format code '{{{{date:{format_code}}}}}'")
                return match.group(0)

        # Use re.sub to find and replace all placeholders
        try:
            processed_location = re.sub(r"{{date:([^{}]+)}}", replace_date_placeholder, location_template)
        except Exception as regex_e:
            logger.warning(f"Error processing daily_note_location template '{location_template}'. Using as is. Error: {regex_e}")
            processed_location = location_template # Fallback

        if processed_location == "/" or processed_location == "." or not processed_location:
            relative_path = filename
        else:
            # Join the processed location with the filename
            relative_path = os.path.join(processed_location, filename)
        # --- End location formatting ---

        # Normalize path separators
        return relative_path.replace('\\', '/')

    except ValueError as e: # Catch invalid date format errors
        raise VaultError(f"Invalid date format or value for daily note path: {target_date}") from e
    except Exception as e:
        raise VaultError(f"Error calculating daily note path for {target_date}: {e}") from e

def create_daily_note(target_date=None, force_create=False):
    """Creates a daily note for the given date if it doesn't exist.

    Uses the configured template if available.

    Args:
        target_date: A datetime.date object. Defaults to today.
        force_create: If True, creates the note even if it exists (potentially dangerous!). Defaults to False.

    Returns:
        The relative path of the created or existing note, or None on error.
    """
    try:
        relative_path = get_daily_note_path(target_date)
    except VaultError as e:
        # Propagate path calculation errors
        raise VaultError(f"Failed to get daily note path for {target_date}: {e}") from e

    full_path = resolve_vault_path(relative_path, require_note=True)

    if os.path.exists(full_path) and not force_create:
        # print(f"Daily note already exists: {relative_path}") # Less verbose
        return relative_path # Return path if already exists

    # Determine content (template or empty)
    content = ""
    if DAILY_NOTE_TEMPLATE_PATH:
        try:
            template_full_path = resolve_vault_path(DAILY_NOTE_TEMPLATE_PATH)
        except InvalidPathError:
            template_full_path = None
        if template_full_path and os.path.isfile(template_full_path):
            try:
                with open(template_full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # print(f"Using template: {DAILY_NOTE_TEMPLATE_PATH}")
            except Exception as e:
                logger.warning(f"Failed to read template {DAILY_NOTE_TEMPLATE_PATH}: {e}. Creating empty.")
        else:
            logger.warning(f"Template not found or invalid: {DAILY_NOTE_TEMPLATE_PATH}. Creating empty.")

    try:
        # create_note raises InvalidPathError, NoteCreationError, MetadataError, VaultError
        if create_note(relative_path, content, metadata=None):
            # print(f"Daily note created: {relative_path}")
            return relative_path
        else:
            # Should not happen if create_note raises exceptions
             raise NoteCreationError(f"create_note returned False unexpectedly for {relative_path}")
    except (InvalidPathError, NoteCreationError, MetadataError, VaultError) as e:
        # Propagate specific errors from create_note
        raise e
    except Exception as e:
        # Catch other unexpected errors during creation
        raise NoteCreationError(f"Unexpected error creating daily note {relative_path}: {e}") from e

def append_to_daily_note(content_to_append, target_date=None, backup=True):
    """Appends content to the daily note for the given date.

    Creates the daily note if it doesn't exist.

    Args:
        content_to_append: The string content to append.
        target_date: A datetime.date object. Defaults to today.
        backup: If True (default), creates a backup before appending (if note exists).

    Returns:
        True if append was successful, False otherwise.
    """
    try:
        # Ensure the daily note exists, get its path
        relative_path = create_daily_note(target_date, force_create=False)
    except (VaultError, NoteCreationError) as e:
        # Failed to get/create the note path
        raise VaultError(f"[AppendDaily] Failed to find or create daily note for {target_date or 'today'}: {e}") from e

    try:
        # append_to_note raises InvalidPathError, NoteNotFoundError, BackupError, VaultError
        if append_to_note(relative_path, content_to_append, backup=backup):
             return True
        else:
            # Should not happen if append_to_note raises exceptions
            raise VaultError(f"append_to_note returned False unexpectedly for {relative_path}")
    except (InvalidPathError, NoteNotFoundError, BackupError, VaultError) as e:
        # Propagate specific errors
        raise e
    except Exception as e:
        raise VaultError(f"[AppendDaily] Unexpected error appending to {relative_path}: {e}") from e


# --- Add other daily note functions below ---
