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

1.  **Clone the repository** (if you haven't already):
    ```bash
    # git clone <repository-url>
    # cd OMCP 
    ```

2.  **Navigate to the project directory**:
    ```bash
    cd /path/to/your/OMCP 
    ```

3.  **Create a Python virtual environment** (recommended to avoid dependency conflicts):
    ```bash
    python -m venv .venv 
    ```

4.  **Activate the virtual environment**:
    *   On Windows PowerShell:
        ```powershell
        .venv\Scripts\Activate.ps1 
        ```
    *   On Linux/macOS:
        ```bash
        source .venv/bin/activate 
        ```
    (Your terminal prompt should now show `(.venv)` at the beginning)

5.  **Install the package** and its dependencies:
    ```bash
    pip install . 
    ```

## Configuration

This server is configured using environment variables, which can be conveniently managed using a `.env` file in the project root.

1.  **Copy the example file:**
    ```bash
    # From the project root directory (OMCP/)
    cp .env.example .env 
    ```
    (On Windows, you might use `copy .env.example .env`)

2.  **Edit the `.env` file:**
    Open the newly created `.env` file in a text editor.

3.  **Set `OMCP_VAULT_PATH`:** This is the only **required** variable. Update it with the **absolute path** to your Obsidian vault. Use forward slashes (`/`) for paths, even on Windows.
    ```dotenv
    OMCP_VAULT_PATH="/path/to/your/Obsidian/Vault" 
    ```

4.  **Review Optional Settings:** Adjust the other `OMCP_` variables for daily notes, server port, or backup directory if needed. Read the comments in the file for explanations.

*(Alternatively, instead of using a `.env` file, you can set these as actual system environment variables. The server will prioritize system environment variables over the `.env` file if both are set.)*

## Running Manually (for Testing/Debugging)

While client applications like Claude Desktop will launch the server automatically using the configuration described below, you can also run the server manually from your terminal for direct testing or debugging.

1.  **Ensure Configuration is Done:** Make sure you have created and configured your `.env` file as described in the Configuration section.
2.  **Activate Virtual Environment:**
    ```powershell
    # If not already active
    .venv\Scripts\Activate.ps1 
    ```
    *(Use `source .venv/bin/activate` on Linux/macOS)*
3.  **Run the server script:**
    ```bash
    (.venv) ...> python obsidian_mcp_server/main.py 
    ```

The server will start and print the address it's listening on (e.g., `http://127.0.0.1:8001`). You would typically press `Ctrl+C` to stop it when finished testing.

**Remember:** If you intend to use this server with Claude Desktop or a similar launcher, you should **not** run it manually like this. Configure the client application instead (see next section), and it will handle starting and stopping the server process.

## Client Configuration (Example: Claude Desktop)

Many MCP clients (like Claude Desktop) can launch server processes directly. To configure such a client, you typically need to edit its JSON configuration file (e.g., `claude_desktop_config.json` on macOS/Linux, find the equivalent path on Windows under `AppData`).

You need to provide the command to run the Python interpreter *from the virtual environment* and the path to the server's `main.py` script.

Here's an example entry to add under the `mcpServers` key in the client's JSON configuration:

```json
{
  "mcpServers": {
    // ... other potential servers ...

    "obsidian_vault": { // Choose a descriptive name
      "command": "/path/to/your/project/OMCP/.venv/bin/python", // Linux/macOS Example
      // OR
      // "command": "C:\\path\\to\\your\\project\\OMCP\\.venv\\Scripts\\python.exe", // Windows Example (Note escaped backslashes)
      
      "args": [
        "/path/to/your/project/OMCP/obsidian_mcp_server/main.py" // Linux/macOS Example
        // OR
        // "args": ["C:\\path\\to\\your\\project\\OMCP\\obsidian_mcp_server\\main.py"] // Windows Example
      ],
      
      // Optional but RECOMMENDED: Pass vault path via environment
      "env": { 
        "OMCP_VAULT_PATH": "/path/to/your/Obsidian/Vault" // Linux/macOS Example
        // OR
        // "OMCP_VAULT_PATH": "C:/path/to/your/Obsidian/Vault" // Windows Example (Forward slashes often work better in env vars)
        
        // Add other OMCP_* variables from your .env file if needed/desired
        // "OMCP_DAILY_NOTE_LOCATION": "Journal/Daily"
      }
    }

  }
}
```

**Key Points:**

*   Replace `/path/to/your/project/OMCP/` and `/path/to/your/Obsidian/Vault` with the **absolute paths** relevant to your system.
*   The `command` path **must** point to the `python` (or `python.exe`) executable *inside* the `.venv` you created for this project.
*   The `args` path **must** point to the `main.py` file within the `obsidian_mcp_server` subfolder.
*   Using the `env` block is the most reliable way to ensure the server finds your vault path when launched by the client.
*   Remember to **restart the client application** (e.g., Claude Desktop) after modifying its JSON configuration.

## Available MCP Tools

*   `list_folders`
*   `list_notes`
*   `get_note_content`
*   `get_note_metadata`
*   `get_outgoing_links`
*   `get_backlinks`
*   `get_all_tags`
*   `search_notes_content`
*   `search_notes_metadata`
*   `search_folders`
*   `create_note`
*   `edit_note`
*   `append_to_note`
*   `update_note_metadata`
*   `delete_note`
*   `get_daily_note_path`
*   `create_daily_note`
*   `append_to_daily_note`

## Roadmap

This project is actively developed. Here's a look at planned features:

**v1.x (Near Term)**

*   **Template-Based Note Creation:**
    *   Configure a template directory (`OMCP_TEMPLATE_DIR`).
    *   Implement `create_note_from_template` tool (using template name, target path, optional metadata).
    *   Add tests for template creation.
*   **Folder Creation:**
    *   Implement `create_folder` utility function.
    *   Implement `create_folder` MCP tool.
    *   Add tests for folder creation.

**v1.y (Mid Term / Future Enhancements)**

*   Variable substitution in templates (e.g., `{{DATE}}`).
*   `list_templates` tool.
*   Advanced note update tools (e.g., `append_to_note_by_metadata`).
*   Comprehensive testing review and expansion.

**v2.x+ (Potential Ideas / Longer Term)**

*   **Organization Tools:**
    *   `move_item(source, destination)` (Initial version might not update links).
    *   `rename_item(path, new_name)` (Initial version might not update links).
*   **Content Manipulation Tools:**
    *   `replace_text_in_note(path, old, new, count)`.
    *   `prepend_to_note(path, content)`.
    *   `append_to_section(path, heading, content)` (Requires reliable heading parsing).
*   **Querying Tools:**
    *   `get_local_graph(path)` (Combine outgoing/backlinks).
    *   `search_notes_by_metadata_field(key, value)`.

**Contributions Welcome!**

If you have ideas or want to contribute, please check out the GitHub issues and discussions!