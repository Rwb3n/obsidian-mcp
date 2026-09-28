import os
import shutil
import datetime
import yaml # Needed for writing metadata later
import logging # Import logging
# Import config and exceptions
from obsidian_mcp_server.config import settings
from obsidian_mcp_server.utils.exceptions import VaultError, NoteNotFoundError, InvalidPathError, MetadataError, BackupError, NoteCreationError
from obsidian_mcp_server.utils.frontmatter import split_frontmatter, render_frontmatter
from obsidian_mcp_server.utils.paths import resolve_vault_path, vault_root

logger = logging.getLogger(__name__) # Get logger for this module


# --- Backup Function ---

def _create_backup(relative_note_path):
    """Creates a timestamped backup of a note in the .vault_backups directory.

    Args:
        relative_note_path: The path to the note file relative to the vault root.

    Returns:
        True if backup was successful, False otherwise.
    """
    source_full_path = resolve_vault_path(relative_note_path)
    if not os.path.isfile(source_full_path):
        # Don't raise NoteNotFoundError here? Maybe backup shouldn't fail if note gone.
        logger.warning(f"[Backup] Source file not found, cannot create backup: {relative_note_path}")
        return False # Indicate backup wasn't created, but maybe allow operation?

    try:
        # Construct backup path
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_filename = f"{os.path.basename(relative_note_path)}.{timestamp}.bak"
        # Preserve directory structure within backup folder
        root = vault_root()
        relative_dir = os.path.dirname(os.path.relpath(source_full_path, root))
        backup_subdir = os.path.join(root, settings.backup_dir_name, relative_dir)
        backup_full_path = os.path.join(backup_subdir, backup_filename)

        # Create backup directory if it doesn't exist
        os.makedirs(backup_subdir, exist_ok=True)

        # Copy the file, preserving metadata
        shutil.copy2(source_full_path, backup_full_path)
        # print(f"Backup created for {relative_note_path} at {backup_full_path}") # Less verbose
        return True

    except Exception as e:
        raise BackupError(f"Error creating backup for {relative_note_path}: {e}") from e


def create_note(relative_note_path, content="", metadata=None):
    """Creates a new note file with optional YAML frontmatter.

    Args:
        relative_note_path: The path for the new note, relative to the vault root.
                            Should include the .md extension.
        content: The main markdown content for the note.
        metadata: A dictionary of metadata to include as YAML frontmatter.

    Returns:
        True if note creation was successful, False otherwise.
    """
    full_path = resolve_vault_path(relative_note_path, require_note=True)
    if os.path.exists(full_path):
        raise NoteCreationError(f"[Create] File already exists: {relative_note_path}")

    try:
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(full_path)
        os.makedirs(parent_dir, exist_ok=True)

        # Format the content with frontmatter
        file_content = ""
        if metadata and isinstance(metadata, dict):
            try:
                # Ensure proper YAML formatting, especially for multiline strings
                # PyYAML's dump usually adds a trailing newline
                file_content = render_frontmatter(metadata) + "\n"
            except yaml.YAMLError as e:
                raise MetadataError(f"[Create] Failed to dump YAML metadata for {relative_note_path}: {e}") from e

        file_content += content

        # Write the file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(file_content)

        # print(f"Note created successfully: {relative_note_path}")
        return True # Success

    except MetadataError: # Propagate
        raise
    except Exception as e:
        raise NoteCreationError(f"Error creating note {relative_note_path}: {e}") from e


def edit_note(relative_note_path, new_content, backup=True):
    """Overwrites an existing note with new content.

    Args:
        relative_note_path: The path to the note file relative to the vault root.
        new_content: The new full content for the note.
        backup: If True (default), creates a backup before editing.

    Returns:
        True if the note was edited successfully, False otherwise.
    """
    full_path = resolve_vault_path(relative_note_path, require_note=True)
    if not os.path.isfile(full_path):
        raise NoteNotFoundError(f"[Edit] File does not exist: {relative_note_path}")

    if backup:
        try:
            if not _create_backup(relative_note_path):
                # If backup returns False (e.g. source gone), maybe proceed?
                # For now, let's treat it as an error preventing edit.
                 raise BackupError(f"[Edit] Backup failed or source missing for {relative_note_path}. Aborting edit.")
        except BackupError: # Propagate backup errors
            raise

    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        # print(f"Note edited successfully: {relative_note_path}")
        return True
    except Exception as e:
        raise VaultError(f"Error writing edited note {relative_note_path}: {e}") from e


def append_to_note(relative_note_path, content_to_append, backup=True):
    """Appends content to the end of an existing note using 'ab' mode.

    Args:
        relative_note_path: The path to the note file relative to the vault root.
        content_to_append: The string content to append to the note.
        backup: If True (default), creates a backup before modifying.

    Returns:
        True if the content was appended successfully.
    Raises:
        NoteNotFoundError, InvalidPathError, BackupError, VaultError
    """
    full_path = resolve_vault_path(relative_note_path, require_note=True)
    if not os.path.isfile(full_path):
        raise NoteNotFoundError(f"[Append] File does not exist: {relative_note_path}")

    # Perform backup BEFORE opening the file for modification
    if backup:
        try:
            if os.path.getsize(full_path) > 0:
                if not _create_backup(relative_note_path):
                     raise BackupError(f"[Append] Backup failed or source missing for {relative_note_path}. Aborting append.")
        except BackupError:
            raise # Propagate
        except Exception as backup_e:
             raise BackupError(f"[Append] Error during backup process for {relative_note_path}: {backup_e}") from backup_e

    try:
        # Open directly in append binary ('ab') mode. No reading/seeking.
        with open(full_path, 'ab') as f_append:
            # Always add a newline before appending to ensure separation.
            # This might create an extra blank line if one already existed.
            f_append.write(b'\n')
            # Write the content (encoded)
            f_append.write(content_to_append.encode('utf-8'))
        return True
    except IOError as e:
        raise VaultError(f"IOError appending to note {relative_note_path}: {e}") from e
    except Exception as e:
        raise VaultError(f"Unexpected error appending to note {relative_note_path}: {e}") from e


def update_metadata(relative_note_path, metadata_updates, backup=True):
    """Updates the YAML frontmatter of an existing note.

    Args:
        relative_note_path: Path to the note relative to the vault root.
        metadata_updates: Dictionary of metadata keys/values to add or overwrite.
        backup: If True (default), creates a backup before updating.

    Returns:
        True if metadata updated successfully.
    Raises:
        NoteNotFoundError: If the note cannot be found.
        InvalidPathError: If the path is outside the vault.
        MetadataError: If YAML parsing/dumping fails.
        BackupError: If backup fails during the edit.
        VaultError: For other vault access issues.
    """
    full_path = resolve_vault_path(relative_note_path, require_note=True)
    # Check existence early - Reading below will fail anyway, but this is clearer.
    if not os.path.isfile(full_path):
         raise NoteNotFoundError(f"[Meta] Note not found for reading: {relative_note_path}")

    try: # Outer try block for the whole operation
        # --- Step 1: Read existing content ---
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
             # Catch read errors specifically
             raise VaultError(f"[Meta] Error reading note {relative_note_path}: {e}") from e

        # --- Step 2: Parse existing metadata & body ---
        # A block that is not a mapping (e.g. text between horizontal rules) is body, not metadata.
        # Invalid YAML aborts the update rather than discarding the existing frontmatter.
        try:
            existing_metadata, _, body_content = split_frontmatter(content)
        except yaml.YAMLError as e:
            raise MetadataError(f"[Meta] Existing frontmatter in {relative_note_path} is not valid YAML; refusing to overwrite it: {e}") from e

        # --- Step 3: Update metadata dictionary ---
        updated_metadata = dict(existing_metadata or {})
        updated_metadata.update(metadata_updates)

        # --- Step 4: Construct new content string ---
        new_full_content = ""
        if updated_metadata:
            try:
                new_full_content = render_frontmatter(updated_metadata) + body_content
            except yaml.YAMLError as e:
                # Raise specific error for YAML dumping failure
                raise MetadataError(f"[Meta] Failed to dump updated YAML for {relative_note_path}: {e}") from e
        else:
            # If no metadata after update, just write the body content back
            new_full_content = body_content

        # --- Step 5: Perform Backup ---
        if backup:
            try:
                if not _create_backup(relative_note_path):
                     raise BackupError(f"[Meta] Backup failed or source missing for {relative_note_path}. Aborting update.")
            except BackupError:
                raise # Propagate
            except Exception as backup_e:
                 raise BackupError(f"[Meta] Error during backup process for {relative_note_path}: {backup_e}") from backup_e

        # --- Step 6: Write back updated content ---
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_full_content)

        return True

    # Handle specific errors caught during steps
    except (NoteNotFoundError, InvalidPathError, MetadataError, BackupError, VaultError) as e:
        raise e # Re-raise known errors
    except Exception as e:
        # Catch any other unexpected errors during the process
        raise VaultError(f"[Meta] Unexpected error updating metadata for {relative_note_path}: {e}") from e


def delete_note(relative_note_path: str, backup: bool = True) -> bool:
    """Deletes a note file, optionally creating a backup first.

    Args:
        relative_note_path: Path to the note relative to the vault root.
        backup: If True (default), creates a backup before deleting.

    Returns:
        True if deletion was successful.
    Raises:
        NoteNotFoundError: If the note cannot be found.
        InvalidPathError: If the path is outside the vault.
        BackupError: If backup is requested and fails.
        VaultError: For other vault access/deletion issues.
    """
    # 1. Path Validation
    full_path = resolve_vault_path(relative_note_path, require_note=True)

    # 2. Check Existence
    if not os.path.isfile(full_path):
        raise NoteNotFoundError(f"[Delete] Note not found: {relative_note_path}")

    # 3. Perform Backup (if requested)
    if backup:
        try:
            if not _create_backup(relative_note_path):
                # If backup fails (e.g., permissions, disk space), stop the deletion.
                raise BackupError(f"[Delete] Backup failed for {relative_note_path}. Aborting deletion.")
        except BackupError:
            raise # Propagate
        except Exception as backup_e:
            raise BackupError(f"[Delete] Error during backup process for {relative_note_path}: {backup_e}") from backup_e

    # 4. Delete the File
    try:
        logger.debug(f"[Delete] Attempting to delete file: {full_path}") # Log before delete
        os.remove(full_path)
        logger.debug(f"[Delete] os.remove completed for: {full_path}") # Log after delete
        # Add explicit check
        if not os.path.exists(full_path):
            logger.info(f"[Delete] Verified file does not exist after removal: {relative_note_path}")
            return True
        else:
            logger.error(f"[Delete] CRITICAL: os.remove ran but file still exists: {full_path}")
            # Treat this as a failure
            raise VaultError(f"[Delete] File reportedly still exists after os.remove attempt: {relative_note_path}")

    except OSError as e:
        # Handle potential errors during deletion (e.g., permissions)
        logger.error(f"[Delete] OSError during os.remove for {full_path}: {e}") # Log specific OS error
        raise VaultError(f"[Delete] Failed to delete note file {relative_note_path}: {e}") from e
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"[Delete] Unexpected error during deletion process for {full_path}: {e}") # Log other errors
        raise VaultError(f"[Delete] Unexpected error deleting note {relative_note_path}: {e}") from e


# --- Add other writer functions below ---
