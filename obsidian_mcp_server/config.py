"""Configuration loading for the Obsidian MCP Server."""

import os
import logging
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Defines application settings, loadable from env vars or .env file."""

    # Define fields with type hints and default values
    # Environment variables will automatically override defaults (case-insensitive)
    # e.g., setting OBSIDIAN_VAULT_PATH in .env or env vars will override default.
    
    # --- Server Configuration ---
    server_host: str = "127.0.0.1" # Default host
    server_port: int = 8001      # Default port
    # stdio for clients that launch the server (e.g. Claude Desktop); sse/streamable-http to listen on host:port
    server_transport: Literal["stdio", "sse", "streamable-http"] = "stdio"

    # --- Vault Configuration ---
    # Required. Read from OMCP_VAULT_PATH (documented) or OMCP_OBSIDIAN_VAULT_PATH.
    obsidian_vault_path: str = Field(validation_alias=AliasChoices("OMCP_VAULT_PATH", "OMCP_OBSIDIAN_VAULT_PATH"))

    # --- Daily Note Configuration ---
    daily_note_location: str = "Journal/Daily" # Default to Vault Root
    daily_note_format: str = "%Y-%m-%d" # Default to YYYY-MM-DD
    daily_note_template_path: Optional[str] = Field(
        default=None, # Default to no template
        validation_alias=AliasChoices("OMCP_DAILY_NOTE_TEMPLATE", "OMCP_DAILY_NOTE_TEMPLATE_PATH"),
    )

    # --- Backup Configuration ---
    backup_dir_name: str = "_mcp_backups"

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file='.env',          # Load .env file if it exists
        env_file_encoding='utf-8',
        extra='ignore',            # Ignore extra fields from env/file
        env_prefix='OMCP_',        # Prefix for environment variables
        case_sensitive=False      # Case-insensitive environment variable matching
    )

# Create a single instance of the settings to be imported by other modules
settings = Settings()

# --- Optional: Add some validation or path resolution logic here ---
# Resolve vault path to a canonical absolute path immediately
settings.obsidian_vault_path = os.path.realpath(settings.obsidian_vault_path)
if not os.path.isdir(settings.obsidian_vault_path):
    raise ValueError(f"OMCP_VAULT_PATH does not point to a directory: {settings.obsidian_vault_path}")

# Example: Basic validation for daily note location (more complex needed for {{date}} syntax)
if settings.daily_note_location not in ["/", "."] and not os.path.isdir(os.path.join(settings.obsidian_vault_path, settings.daily_note_location)):
    # Check if it's a *potential* directory within the vault, even if it doesn't exist yet
    potential_path = os.path.abspath(os.path.join(settings.obsidian_vault_path, settings.daily_note_location))
    if not potential_path.startswith(settings.obsidian_vault_path):
         logger.warning(f"Daily note location '{settings.daily_note_location}' seems invalid or outside vault. Defaulting to root.")
         settings.daily_note_location = "/"
    # Else: Assume it's a valid relative path that might be created later #

# print(f"Configuration loaded. Vault Path: {settings.obsidian_vault_path}") # REMOVED - Interferes with MCP stdio communication #

# print(f"Configuration loaded:") # REMOVED - Interferes with MCP stdio communication
# print(f"- Vault Path: {settings.obsidian_vault_path}") # REMOVED
# print(f"- Daily Location: {settings.daily_note_location}") # REMOVED
# print(f"- Daily Format: {settings.daily_note_format}") # REMOVED
# print(f"- Daily Template: {settings.daily_note_template_path}") # REMOVED
# print(f"- Backup Dir: {settings.backup_dir_name}") # REMOVED
# # Print new settings
# print(f"- Server Host: {settings.server_host}") # REMOVED
# print(f"- Server Port: {settings.server_port}") # REMOVED

# The block starting from here down uses incorrect attribute names (omcp_*) and will be removed.
# // ... existing code ... 