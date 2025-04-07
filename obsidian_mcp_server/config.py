"""Configuration loading for the Obsidian MCP Server."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """Defines application settings, loadable from env vars or .env file."""

    # Define fields with type hints and default values
    # Environment variables will automatically override defaults (case-insensitive)
    # e.g., setting OBSIDIAN_VAULT_PATH in .env or env vars will override default.
    
    # --- Server Configuration ---
    server_host: str = "127.0.0.1" # Default host
    server_port: int = 8001      # Default port

    # --- Vault Configuration ---
    # Use the path we established earlier as the default
    obsidian_vault_path: str = r"D:\Documents\OBSIDIAN\OBSIDIAN - Copy"

    # --- Daily Note Configuration ---
    daily_note_location: str = "Journal/Daily" # Default to Vault Root
    daily_note_format: str = "%Y-%m-%d" # Default to YYYY-MM-DD
    daily_note_template_path: Optional[str] = None # Default to no template

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
# Example: Resolve vault path to absolute path immediately
settings.obsidian_vault_path = os.path.abspath(settings.obsidian_vault_path)

# Example: Basic validation for daily note location (more complex needed for {{date}} syntax)
if settings.daily_note_location not in ["/", "."] and not os.path.isdir(os.path.join(settings.obsidian_vault_path, settings.daily_note_location)):
    # Check if it's a *potential* directory within the vault, even if it doesn't exist yet
    potential_path = os.path.abspath(os.path.join(settings.obsidian_vault_path, settings.daily_note_location))
    if not potential_path.startswith(settings.obsidian_vault_path):
         print(f"Warning: Daily note location '{settings.daily_note_location}' seems invalid or outside vault. Defaulting to root.")
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