import os
import logging
import shutil
import yaml
from datetime import datetime
from typing import Any, Optional, Dict

# Define VaultError at the top
class VaultError(Exception):
    """Custom exception for vault operations."""
    pass

# Configure logging
logger = logging.getLogger(__name__)

def _get_full_path(vault_path: str, relative_path: str) -> str | None:
    """Constructs the full absolute path and validates it."""
    try:
        # Normalize separators and clean the path
        norm_rel_path = os.path.normpath(relative_path)
        # Prevent escaping the vault
        if norm_rel_path.startswith("..") or os.path.isabs(norm_rel_path):
            logger.error(f"Invalid relative path (potential escape): {relative_path}")
            return None
        full_path = os.path.join(vault_path, norm_rel_path)
        # Ensure the final path is still within the vault (redundancy is good)
        if not os.path.abspath(full_path).startswith(os.path.abspath(vault_path)):
            logger.error(f"Path escape detected: {full_path}")
            return None
        return full_path
    except Exception as e:
        logger.error(f"Error constructing full path for {relative_path}: {e}")
        return None

def _create_backup(
    file_path: str, backup_dir: str | None
) -> bool | VaultError:
    """Creates a timestamped backup of a file."""
    if not backup_dir:
        # Should have been set by caller, but double-check
        logger.error("Backup directory not provided.")
        return VaultError("Backup directory missing")

    if not os.path.exists(file_path):
        logger.warning(f"Backup skipped: File does not exist at {file_path}")
        return True # No file to backup, technically not an error here

    if not os.path.isfile(file_path):
         logger.error(f"Backup failed: Path is not a file {file_path}")
         return VaultError("Backup failed: Path is not a file")

    # Check file size - skip backup for empty files if desired (optional)
    # if os.path.getsize(file_path) == 0:
    #     logger.debug(f"Backup skipped: File is empty {file_path}")
    #     return True

    try:
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_filename = f"{os.path.basename(file_path)}.{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Backup created: {backup_path}")
        return True
    except OSError as e:
        logger.error(f"OS error creating backup for {file_path}: {e}")
        return VaultError(f"Backup OS error: {e}")
    except Exception as e:
        logger.error(f"Failed to create backup for {file_path}: {e}")
        return VaultError(f"Backup failed: {e}")

def create_note(
    note_path: str,
    content: str,
    vault_path: str,
    metadata: Optional[Dict[str, Any]] = None,
    overwrite: bool = False,
    backup: bool = True,
    backup_dir: str | None = None,
) -> bool | VaultError:
    """Creates a new note file with the given content and optional metadata."""
    full_path = _get_full_path(vault_path, note_path)
    if not full_path:
        return VaultError(f"Invalid path generated for {note_path}")

    if os.path.exists(full_path) and not overwrite:
        logger.warning(f"Note creation skipped: File already exists at {full_path}")
        return VaultError("Note already exists")

    # Ensure backup directory is set if needed
    if backup and not backup_dir:
        backup_dir = os.path.join(vault_path, ".backup")

    # Backup before potentially overwriting
    if backup and os.path.exists(full_path) and overwrite:
        backup_result = _create_backup(full_path, backup_dir)
        if isinstance(backup_result, VaultError):
            return backup_result # Propagate backup error

    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(full_path)
        os.makedirs(parent_dir, exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            # --- Add logic to write frontmatter --- 
            if metadata: # Check if metadata was provided
                # Filter out None values before writing initial frontmatter
                filtered_metadata = {k: v for k, v in metadata.items() if v is not None}
                if filtered_metadata:
                    f.write("---\n")
                    yaml.dump(filtered_metadata, f, default_flow_style=False, sort_keys=False)
                    f.write("---\n")
                    # Add a blank line if there is content following
                    if content:
                        f.write("\n") 
            # --- End frontmatter logic ---
            f.write(content)
        logger.info(f"Note created: {full_path}")
        return True
    except OSError as e:
        logger.error(f"OS error creating note: {full_path}: {e}")
        return VaultError(f"File system error: {e}")
    except yaml.YAMLError as e: # Add YAML error handling for writing
         logger.error(f"Error writing YAML frontmatter during create for {note_path}: {e}")
         # Attempt to clean up the partially created file?
         try: 
             if os.path.exists(full_path):
                 os.remove(full_path)
         except Exception as cleanup_e:
             logger.error(f"Failed to cleanup partially created file {full_path} after YAML error: {cleanup_e}")
         return VaultError(f"YAML write error: {e}")
    except Exception as e:
        logger.error(f"Failed to create note: {full_path}: {e}")
        return VaultError(f"Unexpected error creating note: {e}")

def edit_note(
    note_path: str,
    content: str,
    vault_path: str,
    backup: bool = True,
    backup_dir: str | None = None,
) -> bool | VaultError:
    """Overwrites an existing note with new content."""
    full_path = _get_full_path(vault_path, note_path)
    if not full_path:
        return VaultError(f"Invalid path generated for {note_path}")

    if not os.path.exists(full_path):
        return VaultError(f"Note does not exist: {full_path}")
    if not os.path.isfile(full_path):
        return VaultError(f"Path is not a file: {full_path}")

    # Ensure backup directory is set if needed
    if backup and not backup_dir:
        backup_dir = os.path.join(vault_path, ".backup")

    # Create backup before editing
    if backup:
        backup_result = _create_backup(full_path, backup_dir)
        if isinstance(backup_result, VaultError):
            return backup_result # Propagate backup error

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Note edited: {full_path}")
        return True
    except OSError as e:
        logger.error(f"OS error editing note: {full_path}: {e}")
        return VaultError(f"File system error: {e}")
    except Exception as e:
        logger.error(f"Failed to edit note: {full_path}: {e}")
        return VaultError(f"Unexpected error editing note: {e}")

def update_metadata(
    note_path: str,
    metadata: dict[str, Any],
    vault_path: str,
    backup: bool = True,
    backup_dir: str | None = None,
) -> bool | VaultError:
    """Updates the YAML frontmatter of a note."""
    full_path = _get_full_path(vault_path, note_path)
    if not full_path:
        return VaultError(f"Invalid path generated for {note_path}")

    if not os.path.exists(full_path):
        return VaultError(f"Note does not exist: {full_path}")
    if not os.path.isfile(full_path):
        return VaultError(f"Path is not a file: {full_path}")

    # Ensure backup directory is set if needed
    if backup and not backup_dir:
        backup_dir = os.path.join(vault_path, ".backup")

    # Backup before modifying
    if backup:
        backup_result = _create_backup(full_path, backup_dir)
        if isinstance(backup_result, VaultError):
            return backup_result # Propagate backup error

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        content_start_index = 0
        current_frontmatter = {}
        if lines and lines[0].strip() == "---":
            try:
                end_marker_index = -1
                for i, line in enumerate(lines[1:], start=1):
                    if line.strip() == "---":
                        end_marker_index = i
                        break
                if end_marker_index > 0:
                    frontmatter_str = "".join(lines[1:end_marker_index])
                    parsed_yaml = yaml.safe_load(frontmatter_str)
                    if isinstance(parsed_yaml, dict):
                        current_frontmatter = parsed_yaml
                    else:
                        logger.warning(f"Existing frontmatter in {note_path} is not a dict, overwriting.")
                    content_start_index = end_marker_index + 1
            except yaml.YAMLError as e:
                logger.error(f"Error parsing existing YAML frontmatter in {note_path}: {e}")
                return VaultError(f"YAML parse error: {e}")
            except Exception as e: # Catch other potential errors during parsing
                 print(f"DEBUG PRINT --> update_metadata: Unexpected error reading existing frontmatter in {note_path}: {e}")
                 return VaultError(f"Frontmatter read error: {e}")
        
        initial_frontmatter_loaded = current_frontmatter.copy() 
        logger.debug(f"--> update_metadata: Initial loaded frontmatter: {initial_frontmatter_loaded}") 
        logger.debug(f"--> update_metadata: Input metadata updates: {metadata}") 

        # --- Corrected Merge Logic --- 
        # Start with the loaded frontmatter (current_frontmatter)
        # Iterate through the input metadata_updates dictionary
        for key, value in metadata.items():
            if value is None:
                # If input value is None, remove the key from current_frontmatter if it exists
                current_frontmatter.pop(key, None) 
            else:
                # Otherwise, update or add the key/value in current_frontmatter
                current_frontmatter[key] = value
        # current_frontmatter now contains original + updated/added - removed keys
        # --- End Corrected Merge Logic ---

        final_frontmatter_to_write = {k: v for k, v in current_frontmatter.items() if v is not None} # Explicitly filter None before dump
        logger.debug(f"--> update_metadata: Final frontmatter AFTER None filtering: {final_frontmatter_to_write}") 

        with open(full_path, "w", encoding="utf-8") as f:
            # Revert to using yaml.dump
            if final_frontmatter_to_write:
                f.write("---\n")
                yaml.dump(final_frontmatter_to_write, f, default_flow_style=False, sort_keys=False) # USE YAML.DUMP AGAIN
                f.write("---\n")
                # Add a blank line after frontmatter if there's content following
                if content_start_index < len(lines) and lines[content_start_index].strip() != "":
                     f.write("\n")

            # Write the rest of the content
            f.writelines(lines[content_start_index:])

        logger.info(f"Metadata updated for note: {full_path}")
        # Return True on success
        return True

    except OSError as e:
        logger.error(f"OS error updating metadata: {full_path}: {e}")
        return VaultError(f"File system error: {e}")
    except Exception as e:
        logger.error(f"Failed to update metadata: {full_path}: {e}")
        return VaultError(f"Unexpected error updating metadata: {e}")

def delete_note(
    note_path: str,
    vault_path: str,
    backup: bool = True,
    backup_dir: str | None = None,
) -> bool | VaultError:
    """Deletes a note file."""
    full_path = _get_full_path(vault_path, note_path)
    if not full_path:
        return VaultError(f"Invalid path generated for {note_path}")

    if not os.path.exists(full_path):
        logger.warning(f"Deletion skipped: Note does not exist at {full_path}")
        return True # File doesn't exist, goal achieved
    if not os.path.isfile(full_path):
        return VaultError(f"Deletion failed: Path is not a file: {full_path}")

    # Ensure backup directory is set if needed
    if backup and not backup_dir:
        backup_dir = os.path.join(vault_path, ".backup")

    # Backup before deleting
    if backup:
        backup_result = _create_backup(full_path, backup_dir)
        if isinstance(backup_result, VaultError):
            # Log backup error but proceed with deletion? Or return error?
            # For now, let's return the error to be safe.
            logger.error(f"Backup failed before deletion, aborting delete for {full_path}: {backup_result}")
            return backup_result

    try:
        os.remove(full_path)
        logger.info(f"Note deleted: {full_path}")
        return True
    except OSError as e:
        logger.error(f"OS error deleting note: {full_path}: {e}")
        return VaultError(f"File system error: {e}")
    except Exception as e:
        logger.error(f"Failed to delete note: {full_path}: {e}")
        return VaultError(f"Unexpected error deleting note: {e}")

def append_to_note(
    note_path: str,
    content: str,
    vault_path: str,
    backup: bool = True,
    backup_dir: str | None = None,
) -> bool | VaultError:
    """Appends content to an existing note. (Simplified for debugging)"""
    full_path = _get_full_path(vault_path, note_path)
    if not full_path:
        return VaultError(f"Invalid path generated for {note_path}")

    if not os.path.exists(full_path):
        return VaultError(f"Note does not exist: {full_path}")
    if not os.path.isfile(full_path):
        return VaultError(f"Path is not a file: {full_path}")

    try:
        # Encode content to bytes using UTF-8
        data = content.encode("utf-8")
    except Exception as e:
        logger.error(f"Failed to encode content for appending: {e}")
        return VaultError(f"Content encoding failed: {e}")

    logger.debug(f"Attempting to append to note (simplified): {full_path}")

    # Re-enable backup check
    if backup: # Check i backup is requested
        # Ensure backup directory is set if needed (copied from create/edit)
        if not backup_dir:
            backup_dir = os.path.join(vault_path, ".backup")
        try:
            backup_result = _create_backup(full_path, backup_dir)
            if isinstance(backup_result, VaultError):
                logger.error(f"Backup failed before append, aborting: {backup_result}")
                return backup_result # Propagate backup error
        except Exception as e:
            logger.error(f"Unexpected error during backup check for append: {e}")
            # Decide if we should proceed without backup or return error
            return VaultError(f"Unexpected backup error: {e}")

    try:
        # logger.debug(f"--> PRE-OPEN: Preparing to open {full_path} in mode 'ab'")
        # Open in append binary mode ('ab') - simplest possible append
        with open(full_path, "ab") as f:
            # logger.debug(f"--> POST-OPEN: Successfully opened {full_path}")
            # Add a newline before appending for safety
            # logger.debug(f"--> PRE-WRITE (newline): Writing b'\\n' to {full_path}")
            f.write(b"\n")
            # logger.debug(f"--> POST-WRITE (newline): Wrote b'\\n' to {full_path}")
            # logger.debug(f"--> PRE-WRITE (data): Writing {len(data)} bytes to {full_path}")
            f.write(data)
            # logger.debug(f"--> POST-WRITE (data): Wrote {len(data)} bytes to {full_path}")
        # logger.debug(f"--> POST-CLOSE: Closed {full_path}")
        logger.debug(f"Appended to note: {full_path}") # Keep standard debug log
        return True # Indicate success
    except OSError as e:
        logger.error(f"OS error appending to note: {full_path}: {e}")
        # *** This is where the io.UnsupportedOperation might occur ***
        # Re-raise as VaultError for consistency
        return VaultError(f"File system error during append: {e}")
    except Exception as e:
        logger.error(f"Failed to append to note: {full_path}: {e}")
        return VaultError(f"Unexpected error appending: {e}")
