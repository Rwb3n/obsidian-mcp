![Obsidian MCP Server Banner](OMCP.png)

# Obsidian MCP Tool Server

[![Security Scan (Trivy + Bandit)](https://github.com/rivassec/obsidian-mcp/actions/workflows/trivy-scan.yml/badge.svg)](https://github.com/rivassec/obsidian-mcp/actions/workflows/trivy-scan.yml)
[![Bandit](https://img.shields.io/badge/Bandit-passed-brightgreen?logo=python&logoColor=white)](https://bandit.readthedocs.io)
[![Trivy](https://img.shields.io/badge/Trivy-passed-blue?logo=datadog&logoColor=white)](https://github.com/aquasecurity/trivy)

This project provides a Model Context Protocol (MCP) server that exposes tools for interacting with an Obsidian vault.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running Manually (for Testing/Debugging)](#running-manually-for-testingdebugging)
- [Client Configuration (Example: Claude Desktop)](#client-configuration-example-claude-desktop)
- [Available MCP Tools](#available-mcp-tools)
- [Roadmap](#roadmap)
- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
- [Contributions Welcome!](#contributions-welcome)

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

⚠️ **Important JSON Formatting Rules:**
1. JSON files **do not** support comments (remove any `//` or `/* */` comments)
2. All strings must be properly quoted with double quotes (`"`)
3. Windows paths must use escaped backslashes (`\\`)
4. Use a JSON validator (like [jsonlint.com](https://jsonlint.com/)) to check your syntax

Here's an example entry to add under the `mcpServers` key in the client's JSON configuration:

```json
{
  "mcpServers": {
    "obsidian_vault": {
      "command": "C:\\path\\to\\your\\project\\OMCP\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\your\\project\\OMCP\\obsidian_mcp_server\\main.py"],
      "env": {
        "OMCP_VAULT_PATH": "C:/path/to/your/Obsidian/Vault",
        "OMCP_DAILY_NOTE_LOCATION": "Journal/Daily"
      }
    }
  }
}
```

**Key Points:**

*   Replace the paths with the **absolute paths** relevant to your system
*   For Windows paths in the `command` and `args` fields:
    *   Use double backslashes (`\\`) for path separators
    *   Include the `.exe` extension for the Python executable
*   For Windows paths in the `env` block:
    *   Use forward slashes (`/`) for better compatibility
    *   Do not include the `.exe` extension
*   The `command` path **must** point to the `python.exe` executable *inside* the `.venv` you created
*   The `args` path **must** point to the `main.py` file within the `obsidian_mcp_server` subfolder
*   Using the `env` block is the most reliable way to ensure the server finds your vault path
*   Remember to **restart the client application** after modifying its JSON configuration

**Common Pitfalls to Avoid:**
1. Don't use single backslashes in Windows paths
2. Don't include comments in the JSON
3. Don't forget to escape backslashes in Windows paths
4. Don't mix forward and backslashes in the same path
5. Don't forget to properly quote all strings

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

For a detailed, phased implementation plan including error handling considerations, please see the [ROADMAP.md](ROADMAP.md) file.

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
*   `list_vault_structure` tool for comprehensive vault hierarchy view.
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
*   **Plugin Integration Tools:**
    *   **Dataview Integration:**
        *   `execute_dataview_query(query_type, query)` - Run Dataview queries and get structured results
        *   `search_by_dataview_field(field, value)` - Search notes by Dataview fields
    *   **Task Management:**
        *   `query_tasks(status, due_date, tags)` - Search and filter tasks across vault
    *   **Kanban Integration:**
        *   `get_kanban_data(board_path)` - Get structured kanban board data
    *   **Calendar Integration:**
        *   `get_calendar_events(start_date, end_date)` - Query calendar events and tasks

## Frequently Asked Questions (FAQ)

### Configuration Issues

**Q: My server can't find my vault. What's wrong?**
A: This is usually due to incorrect path configuration. Check:
1. The `OMCP_VAULT_PATH` in your `.env` file uses forward slashes (`/`) even on Windows
2. The path is absolute (starts from root)
3. The path doesn't end with a trailing slash
4. The vault directory exists and is accessible

**Q: Why am I getting permission errors?**
A: This typically happens when:
1. The vault path points to a restricted directory
2. The Python process doesn't have read/write permissions
3. The vault is in a cloud-synced folder (like OneDrive) that's currently syncing

Try:
1. Moving your vault to local directory
2. Running the server with elevated permissions
3. Checking your antivirus isn't blocking access

### Client Connection Issues

**Q: My AI client can't connect to the server. What should I check?**
A: Verify these common issues:
1. The server is actually running (check terminal output)
2. The port in your client config matches the server's port
3. The Python path in your client config points to the correct virtual environment
4. All environment variables are properly set in the client config

**Q: Why do I get "Connection refused" errors?**
A: This usually means:
1. The server isn't running
2. The port is already in use
3. Firewall is blocking the connection

Try:
1. Check if the server is running: `netstat -ano | findstr :8001` (Windows)
2. Try a different port by setting `OMCP_SERVER_PORT` in your `.env`
3. Temporarily disable firewall to test

**Q: I get "[error] [obsidian_vault] Unexpected token 'S', "Starting O"... is not valid JSON". What's wrong?**
A: This error occurs when the client's JSON configuration file is malformed. Common causes:
1. Missing or extra commas in the JSON
2. Unescaped backslashes in Windows paths
3. Comments in the JSON (JSON doesn't support comments)

Check your client config file (e.g., `claude_desktop_config.json`):
1. Use a JSON validator (like [jsonlint.com](https://jsonlint.com/)) to check syntax
2. For Windows paths, escape backslashes: `"C:\\path\\to\\file"`
3. Remove any comments (// or /* */)
4. Ensure all strings are properly quoted
5. Check that all brackets and braces are properly closed

Example of correct Windows path formatting:
```json
{
  "mcpServers": {
    "obsidian_vault": {
      "command": "C:\\path\\to\\your\\project\\OMCP\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\your\\project\\OMCP\\obsidian_mcp_server\\main.py"]
    }
  }
}
```

**Q: I get a timeout error and "Server disconnected" message. What's happening?**
A: This error pattern (initialization succeeds, then times out after 60 seconds) usually means:
1. The server is already running in another process
2. The port is already in use by another application
3. The server process is being terminated unexpectedly

Try these steps in order:

1. **Check for running server processes:**
   ```powershell
   # On Windows
   netstat -ano | findstr :8001
   # Look for the PID and then:
   taskkill /F /PID <PID>
   ```
   ```bash
   # On Linux/macOS
   lsof -i :8001
   # Look for the PID and then:
   kill -9 <PID>
   ```

2. **Check for other applications using the port:**
   - Close any other applications that might use port 8001
   - This includes other MCP servers, development servers, or any web applications
   - If you're not sure, try changing the port in your `.env`:
     ```dotenv
     OMCP_SERVER_PORT=8002
     ```

3. **Verify server process:**
   - Open Task Manager (Windows) or Activity Monitor (macOS)
   - Look for any Python processes related to the MCP server
   - End any suspicious processes

4. **Check system resources:**
   - Ensure you have enough memory and CPU available
   - Check if any antivirus or security software is blocking the process
   - Verify your Python environment has proper permissions

5. **Reset everything:**
   - Stop the client application
   - Kill any remaining server processes
   - Delete the `.env` file and create a new one from `.env.example`
   - Restart your computer (if other steps don't work)
   - Start fresh with the client application

If the issue persists after trying all these steps, please share:
1. The complete error log
2. The output of `netstat -ano | findstr :8001` (Windows) or `lsof -i :8001` (Linux/macOS)
3. Any error messages from your system's event logs

**Q: The server disconnects immediately with "Server transport closed unexpectedly... process exiting early". What's wrong?**
A: This error means the Python server process crashed almost immediately after being launched by the client. It's not a timeout; the server script itself failed to run or stay running.

Common Causes:
1.  **Incorrect Paths in Client JSON:**
    *   `command` doesn't point to the correct `python.exe` *inside* the `.venv`.
    *   `args` doesn't point to the correct `obsidian_mcp_server/main.py` script.
    *   Incorrect path separators or missing backslash escapes (`\\`) on Windows.
2.  **Missing Dependencies:**
    *   Required packages from `requirements.txt` are not installed in the `.venv`.
    *   The client is launching Python without properly activating the virtual environment.
3.  **Syntax Errors:** A recent code change introduced a Python syntax error.
4.  **Critical Configuration/Permission Error:**
    *   Error reading the `.env` file at startup.
    *   Invalid or inaccessible `OMCP_VAULT_PATH`.
    *   Python process lacks permissions to run or access files.
5.  **Early Unhandled Exception:** An error occurs during initial setup before the server starts listening.

Troubleshooting Steps:
1.  **Verify Client JSON Paths:** Double-check the absolute paths for `command` and `args` in your client's JSON config. Use escaped backslashes (`\\`) for Windows paths.
2.  **Test Manually (Crucial Step):**
    *   Activate the virtual environment in your terminal:
        ```powershell
        # On Windows
        .\.venv\Scripts\activate
        ```
        ```bash
        # On Linux/macOS
        source .venv/bin/activate
        ```
    *   Run the server directly:
        ```bash
        python obsidian_mcp_server/main.py
        ```
    *   Look closely for any error messages printed directly in the terminal. This bypasses the client and often reveals the root cause (like `ImportError`, `SyntaxError`, `FileNotFoundError`).
3.  **Check Dependencies:** With the venv activated, run `pip check` and `pip install -r requirements.txt`.
4.  **Validate `.env` and Vault Path:** Ensure `.env` exists, is readable, and `OMCP_VAULT_PATH` is correct (use forward slashes `/`).
5.  **Review Recent Code Changes:** Check for syntax errors or issues in recently edited Python files.

### Note Operations

**Q: Why can't I create/edit notes in certain folders?**
A: This could be due to:
1. Path security restrictions (trying to write outside vault)
2. Folder permissions
3. File locks from other processes

Try:
1. Using relative paths within your vault
2. Checking folder permissions
3. Closing other programs that might have the files open

**Q: Why are my note updates not being saved?**
A: Common causes:
1. The note path is incorrect
2. The content format is invalid
3. Backup creation failed

Check:
1. The note path exists and is accessible
2. The content is valid markdown
3. The backup directory has write permissions

### Daily Notes

**Q: Why aren't my daily notes being created in the right location?**
A: Verify:
1. `OMCP_DAILY_NOTE_LOCATION` is set correctly in `.env`
2. The path uses forward slashes
3. The target folder exists
4. The date format matches your vault's settings

### General Troubleshooting

**Q: How do I check if the server is working correctly?**
A: Run the test client:
```bash
python test_client.py
```
This will perform a series of operations and report any issues.

**Q: Where can I find error logs?**
A: Check:
1. The terminal where the server is running
2. The backup directory for failed operations
3. The system event logs for permission issues

**Q: How do I reset everything to start fresh?**
A: Try these steps:
1. Stop the server
2. Delete the `.env` file
3. Create a new `.env` from `.env.example`
4. Restart the server

**Contributions Welcome!**

