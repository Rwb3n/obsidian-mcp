# Obsidian MCP Server - Design Document

Following the [LLM Application Development Playbook](../guide.md).

## 1. Project Requirements

**Goal:** Create a Model Context Protocol (MCP) server that allows authorized LLMs to interact with a user's Obsidian vault.

**Core Features (based on readme.md):**

*   **Search:**
    *   Search through Folders.
    *   Search through Markdown notes.
*   **Reading:**
    *   Retrieve complete note contents.
    *   Read note metadata (frontmatter).
    *   Discover links between notes.
    *   Explore tags used across the vault.
*   **Writing:**
    *   Create new notes.
    *   Edit existing notes (with automatic backups).
    *   Append content to existing notes.
    *   Update frontmatter metadata.
*   **Daily Notes:**
    *   Manage daily notes (specific functionality TBD).

**Constraints:**

*   All implemented Python files must adhere to the 200-line limit.
*   The server needs to handle MCP requests (specific protocol details TBD).
*   Operations should be safe (e.g., backups before edits).

## 2. Utility Functions (Initial High-Level Plan)

Based on the requirements, we'll need utility functions (`utils/`) to interact with the Obsidian vault filesystem.

*   **`vault_reader.py`**:
    *   `list_folders(path)`
    *   `list_notes(path)`
    *   `get_note_content(note_path)`
    *   `get_note_metadata(note_path)`
    *   `get_outgoing_links(note_path)`
    *   `get_backlinks(note_path)` *(Deferred - Requires full vault scan, potentially slow)*
    *   `get_all_tags()` *(Deferred - Requires full vault scan, potentially slow)*
*   **`vault_writer.py`**:
    *   `create_note(path, content, metadata)`
    *   `edit_note(path, new_content, backup=True)`
    *   `append_to_note(path, content_to_append)`
    *   `update_metadata(path, metadata_dict)`
    *   `_create_backup(path)` (Internal helper)
*   **`vault_search.py`**:
    *   `search_notes_content(query)`
    *   `search_notes_metadata(query)`
    *   `search_folders(query)`
*   **`daily_notes.py`**:
    *   `get_daily_note_path(date)`
    *   `create_daily_note(date, template)`
    *   `append_to_daily_note(date, content)`

*(Implementation details will follow)*

## 3. Flow Design (Compute)

*(To be defined - will likely involve parsing MCP requests and dispatching to the appropriate utility function)*

## 4. Data Schema (Data)

*(To be defined - likely minimal for this server, focusing on request/response data)*

## 5. Implementation

*(Starts after design finalization)*

## 6. Optimization

*(To be addressed later)*

## 7. Reliability

*(To be addressed later, including error handling and backups)* 