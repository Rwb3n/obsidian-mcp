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

## Running the Server

Once installed and configured, run the server from the project root directory:

```bash
# Make sure your virtual environment is active!
(.venv) ...> python obsidian_mcp_server/main.py 
```

The server will start, typically listening on `http://127.0.0.1:8001` (or the port configured in `.env` / `config.py`). MCP clients can then connect to the server's `/sse` endpoint (e.g., `http://127.0.0.1:8001/sse`) to use the available tools.

**Note:** If running via a client launcher like Claude Desktop, you usually *don't* run this command manually. Instead, you configure the launcher as shown below.

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

- `list_folders`