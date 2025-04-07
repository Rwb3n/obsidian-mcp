import os
import sys
import logging

# Add project root to sys.path to allow importing obsidian_mcp_server modules
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Only import Settings
from obsidian_mcp_server.config import Settings
from obsidian_mcp_server.vault_writer import create_note, edit_note, append_to_note, delete_note, VaultError

# Configure basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting direct vault writer test...")

    try:
        # Instantiate Settings directly to load config
        settings = Settings()
        vault_path = settings.vault_path
        # Use a specific test note path
        test_note_rel_path = "_testing/debug_append_test.md"
        test_note_abs_path = os.path.join(vault_path, test_note_rel_path)

        logger.debug(f"Vault Path: {vault_path}")
        logger.debug(f"Test Note Rel Path: {test_note_rel_path}")
        logger.debug(f"Test Note Abs Path: {test_note_abs_path}")

        # Ensure the _testing directory exists
        os.makedirs(os.path.dirname(test_note_abs_path), exist_ok=True)

        # --- Clean up before starting ---
        logger.info(f"Attempting pre-test cleanup for: {test_note_rel_path}")
        if os.path.exists(test_note_abs_path):
            try:
                delete_note(test_note_rel_path, vault_path)
                logger.info(f"Pre-test cleanup successful for: {test_note_rel_path}")
            except Exception as e:
                logger.warning(f"Pre-test cleanup failed (continuing): {e}")
        else:
            logger.info("Pre-test cleanup: Note does not exist.")

        # --- Test Sequence ---
        # 1. Create Note
        logger.info(f"1. Creating note: {test_note_rel_path}")
        create_result = create_note(test_note_rel_path, "Initial content.", vault_path)
        if isinstance(create_result, VaultError):
            logger.error(f"Create failed: {create_result}")
            return
        logger.info(f"Create successful: {create_result}")

        # 2. Edit Note
        logger.info(f"2. Editing note: {test_note_rel_path}")
        edit_result = edit_note(test_note_rel_path, "Overwritten content.", vault_path)
        if isinstance(edit_result, VaultError):
            logger.error(f"Edit failed: {edit_result}")
            return
        logger.info(f"Edit successful: {edit_result}")

        # 3. Append to Note
        logger.info(f"3. Appending to note: {test_note_rel_path}")
        append_result = append_to_note(test_note_rel_path, "Appended text.", vault_path, backup=False) # Keep backup off to match simplified version
        if isinstance(append_result, VaultError):
            logger.error(f"Append failed: {append_result}")
            # *** THIS IS WHERE THE ERROR OCCURS IN MCP ***
            return
        logger.info(f"Append successful: {append_result}")

        logger.info("Direct vault writer test sequence completed successfully!")

    except VaultError as ve:
        logger.error(f"VaultError during test: {ve}")
    except Exception as e:
        logger.error(f"Unexpected error during test: {e}", exc_info=True)

    # --- Always attempt cleanup ---
    finally:
        logger.info(f"Attempting post-test cleanup for: {test_note_rel_path}")
        if os.path.exists(test_note_abs_path):
            try:
                delete_note(test_note_rel_path, vault_path)
                logger.info(f"Post-test cleanup successful for: {test_note_rel_path}")
            except Exception as e:
                logger.error(f"Post-test cleanup failed: {e}")
        else:
             logger.info("Post-test cleanup: Note does not exist.")

if __name__ == "__main__":
    main() 