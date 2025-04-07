# Investigation Summary: `append_to_note` Error

## Problem Description

During testing (`test_client.py`), the `append_to_note` tool consistently failed with an `io.UnsupportedOperation: not readable` error when called after `create_note` and `edit_note`. This occurred even after simplifying the function to its most basic form using `open(..., 'ab')`.

## Hypotheses Explored

1.  **Function Logic Error:** Incorrect file mode usage (`'ab'`, `'r+b'`, etc.), seeking issues, or character encoding problems within `append_to_note`. (Ruled out by simplification)
2.  **Backup Interference:** The `_create_backup` helper function interfering with file handles. (Ruled out by disabling backups)
3.  **MCP Framework Interference:** The `mcp`/`fastmcp` server framework wrapping the tool call interfering with file handles after the function returns. (Deemed unlikely after reviewing framework source code)
4.  **OS/Locking/Permissions (Windows):** A subtle file locking issue, permission problem, or interaction specific to Windows file system behavior triggered by the test sequence. (Possible)
5.  **Async Context:** Unexpected interactions between standard file I/O and the async event loop used by the server. (Possible, less likely for standard `open`)
6.  **Test Client Sequence:** The specific sequence (create -> edit -> append) leaving the file in a problematic state. (Possible)

## Investigation Steps Taken

1.  **Refactoring `append_to_note`:** Multiple attempts were made to refactor the function using different file modes (`'r+b'`, `'ab'`), adding newline checks, and simplifying to a basic binary append. None resolved the error when run via `test_client.py`.
2.  **Disabling Backup:** The `_create_backup` call within `append_to_note` was temporarily disabled. The error persisted.
3.  **Analyzing MCP Framework Code:** Reviewed relevant source code files (`mcp/server/...`, `mcp/server/fastmcp/...`) within the installed package. Found no evidence that the framework interferes with file handles after the tool function completes its execution.
4.  **Direct Execution Test (`debug_append.py`):** Created a separate script (`debug_append.py`) to call `create_note`, `edit_note`, and `append_to_note` directly, bypassing the MCP client/server. **This script executed successfully without the `io.UnsupportedOperation` error.**

## Conclusion

The successful execution of the file operations via `debug_append.py` strongly suggests that the `io.UnsupportedOperation: not readable` error is **not** inherent to the `append_to_note` function's core logic or standard Python file handling.

The error likely stems from the interaction between the function and the context in which it's executed by the **MCP server framework on Windows**, potentially related to:

*   How the framework manages the execution environment or threads/tasks for tool calls.
*   Subtle interactions with the underlying `anyio`/`trio` event loop affecting file handles unexpectedly.
*   Windows-specific file locking or permissions issues triggered only when run through the server process.

## Next Steps (Post-Refresh)

1.  **Revisit Test Sequence:** Simplify `test_client.py` to call `create_note` then *immediately* `append_to_note` (Investigation Step 4 from `workflow_state.md`) to see if the intermediate `edit_note` call is a factor within the MCP context.
2.  **Granular Logging:** Add more detailed logging *within the MCP context* (Investigation Step 3 from `workflow_state.md`) to pinpoint the exact moment the error occurs relative to the file operations.
3.  **Consider Alternatives:** If the issue persists, explore alternative append strategies that might be less prone to framework/OS interference (e.g., reading the entire content, appending in memory, and rewriting the whole file).
4.  **Report to Framework Maintainers:** If the issue seems specific to the `mcp` framework on Windows, consider reporting it.

## Resolution

The root cause was identified as an argument name mismatch between the `@mcp_app.tool` wrapper function defined in `obsidian_mcp_server/mcp_server.py` and the underlying implementation in `obsidian_mcp_server/vault_writer.py`. The wrapper incorrectly expected `content_to_append` while the implementation expected `content`.

Correcting the wrapper function's signature and the argument passed within it in `mcp_server.py` resolved both the Pydantic validation error and the original `io.UnsupportedOperation` error when run via the MCP server. 