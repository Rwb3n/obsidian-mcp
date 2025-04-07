# Obsidian MCP Tool Server

This project provides a Model Context Protocol (MCP) server that exposes tools for interacting with an Obsidian vault.

## Features

Allows MCP clients (like AI assistants) to:
- Read and write notes
- Manage note metadata (frontmatter)
- List notes and folders
- Search notes by content or metadata
- Manage daily notes
- Get outgoing links, backlinks, and tags

## Installation

```bash
# Clone the repository (if you haven't already)
# git clone <repository-url>
# cd OMCP

# Create and activate a virtual environment (recommended)
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

# Install the package
pip install .
```

## Configuration

Configuration is managed via a `.env` file in the project root. Create this file with the following variables:

```dotenv
# --- Required --- 
# Absolute path to your Obsidian vault
OMCP_VAULT_PATH="D:/Path/To/Your/Obsidian/Vault"

# --- Optional (Daily Notes) ---
# Format for daily note filenames (using strftime directives)
OMCP_DAILY_NOTE_FORMAT="%Y-%m-%d" 
# Relative path within the vault where daily notes are stored (use forward slashes)
OMCP_DAILY_NOTE_LOCATION="Journal/Daily"
# Optional template file (relative path) to use for new daily notes
# OMCP_DAILY_NOTE_TEMPLATE="Templates/Daily Note Template.md"
```

Replace the example paths with your actual vault path and desired daily note settings.

## Running the Server

Once installed and configured, run the server from the project root directory:

```bash
python main.py
```

The server will start, typically listening on `http://127.0.0.1:8000`. MCP clients can then connect to this address to use the available tools.

## Available MCP Tools

- `list_folders`
- `list_notes`
- `get_note_content`
- `get_note_metadata`
- `get_outgoing_links`
- `get_backlinks`
- `get_all_tags`
- `create_note`
- `edit_note`
- `append_to_note`
- `update_note_metadata`
- `delete_note`
- `search_notes_content`
- `search_notes_metadata`
- `search_folders`
- `get_daily_note_path`
- `create_daily_note`
- `append_to_daily_note`