# Obsidian MCP Tool Server - Implementation Roadmap

This roadmap outlines the planned implementation order for new MCP tools and features for the Obsidian MCP Tool Server. Each phase builds upon the previous ones.

**Implementation Philosophy:** This server operates directly on the vault files. While leveraging internal Obsidian functions (like complex templating plugins) might seem appealing, it would require a companion Obsidian plugin, significantly increasing complexity and dependencies. Therefore, this roadmap focuses on implementing necessary vault interactions directly within the server for robustness and self-containment.

**Cross-Cutting Concerns:** Throughout all phases, implementation should include:
*   **Robust Error Handling:** Utilize specific custom exceptions (`VaultError`, `NoteNotFoundError`, `InvalidPathError`, etc.) where appropriate. Provide clear, informative error messages to the client/logs. Gracefully handle expected failure conditions (file not found, permissions, invalid input, configuration issues).
*   **Standard Logging:** Employ Python's `logging` framework to record significant events, configuration loading, tool execution (start/end/success/failure), and detailed error information (including stack traces where helpful).
*   **Edge Case Consideration:** Actively consider and test edge cases (e.g., empty files, missing configuration values, name collisions, non-existent paths).

---

## Phase 1: Core Enhancements & Configuration

*   **Goal:** Add high-value, foundational tools and necessary configuration options, establishing core error handling and logging patterns.
*   **Components:**
    1.  **Configuration Update:**
        *   Add `OMCP_ARCHIVE_PATH` to `config.py` and `.env.example`.
        *   Add `OMCP_TEMPLATE_DIR` to `config.py` and `.env.example`.
        *   **Acceptance:** Settings are loadable, documented in README. Configuration loading logs key values (potentially redacted) and handles missing required settings gracefully.
    2.  **Tool: `patch_metadata_field(path, key, value)`**
        *   **Implementation:** Modify `utils/vault_writer.py`. Leverage existing YAML parsing. Handle adding/updating keys. Handle notes without existing frontmatter.
        *   **Acceptance:** Can add/update a single metadata key; preserves other metadata; handles missing keys/frontmatter; handles YAML parsing errors and file I/O errors; basic YAML validation passes; tests written and pass, including error cases.
    3.  **Tool: `create_folder(path)`**
        *   **Implementation:** Add function to `utils/vault_writer.py`. Use `os.makedirs(exist_ok=True)`. Integrate path validation logic.
        *   **Acceptance:** Can create nested folders; handles existing folders gracefully; respects vault boundaries; handles permission errors; tests written and pass, including error cases.
    4.  **Tool: `archive_note(path)`** (Replaces `archive_or_delete_note` concept)
        *   **Implementation:** Add function to `utils/vault_writer.py`. Use `shutil.move`. Ensure archive directory exists (use `OMCP_ARCHIVE_PATH`). Handle potential name collisions (e.g., append timestamp or error). Log action via standard logging.
        *   **Acceptance:** Moves note to configured archive path; creates archive path if needed; handles collisions as defined; handles file not found, permission errors, archive path configuration errors; tests written and pass, including error cases.
*   **Dependencies:** Requires completion of Phase 1.1 before 1.4.

---

## Phase 2: Templating Core

*   **Goal:** Implement core functionality for creating notes from templates with appropriate error handling.
*   **Components:**
    1.  **Tool: `list_templates()`**
        *   **Implementation:** Add function to `utils/vault_reader.py` (or similar). List files in `OMCP_TEMPLATE_DIR`.
        *   **Acceptance:** Returns list of template filenames; handles non-existent or inaccessible template dir gracefully (logs warning/error, returns empty list or raises specific exception); tests written and pass.
    2.  **Tool: `create_note_from_template(template_name, target_path, metadata_override=None)`**
        *   **Implementation:** Add function to `utils/vault_writer.py`. Read template file content. Perform basic variable substitution (Phase 2.3). Combine with `create_note` logic, potentially overriding template metadata with `metadata_override`.
        *   **Acceptance:** Creates note using template content; substitutes variables; applies metadata override; handles template not found, template read errors, variable substitution errors, and errors from underlying `create_note` operation; tests written and pass, including error cases.
    3.  **Feature: Basic Template Variable Substitution (`{{DATE}}`, `{{TIME}}`, `{{DATETIME}}`)**
        *   **Implementation:** Enhance the template reading logic within `create_note_from_template` to perform simple string replacement for predefined variables.
        *   **Acceptance:** Variables are correctly substituted in created notes. Errors during substitution are handled.

*   **Dependencies:** Phase 1.

---

## Phase 3: Section Manipulation Core

*   **Goal:** Implement tools for safe, targeted modification of note sections, focusing on robust Markdown parsing error handling.
*   **Components:**
    1.  **Utility: `find_section_boundaries(content, heading_text)`**
        *   **Implementation:** Create a robust utility function (e.g., in `utils/markdown_parser.py`) that takes note content and a heading string. Returns the start and end character indices of the content belonging to that section (excluding the heading line itself). Must handle different heading levels (`#`, `##`, etc.) and finding the section end (next heading of same/higher level or EOF).
        *   **Acceptance:** Accurately identifies section boundaries in various test cases (headings at different levels, nested sections, EOF). Returns clear error/indicator (e.g., raise `SectionNotFoundError` exception) if heading is not found.
    2.  **Tool: `append_to_section(path, heading, content)`**
        *   **Implementation:** Add function to `utils/vault_writer.py`. Read note content. Use `find_section_boundaries` utility. Insert `content` at the end boundary index. Write file back. Define behavior if heading not found (e.g., create heading and append, or raise error).
        *   **Acceptance:** Appends content correctly below specified heading; handles heading-not-found case as defined (with appropriate error or creation logic); handles file not found, section finding errors, file write errors; preserves rest of note content; tests written and pass, including error cases.
    3.  **Tool: `patch_note_section(path, heading, content)`**
        *   **Implementation:** Add function to `utils/vault_writer.py`. Read note content. Use `find_section_boundaries` utility. Replace content between start/end boundaries with new `content`. Write file back. Define behavior if heading not found (e.g., raise error).
        *   **Acceptance:** Replaces content correctly under specified heading; handles heading-not-found case as defined (raising specific error); handles file not found, section finding errors, file write errors; preserves rest of note content; tests written and pass, including error cases.

*   **Dependencies:** Phase 3.1 is required for 3.2 and 3.3.

---

## Phase 4: Advanced Querying & Editing

*   **Goal:** Add more specialized search and editing tools with specific error handling for their operations.
*   **Components (Can be implemented in parallel):**
    1.  **Tool: `prepend_to_note(path, content)`**
        *   **Implementation:** `utils/vault_writer.py`. Read, prepend, write. Handle frontmatter correctly (insert after).
        *   **Acceptance:** Prepends content; preserves frontmatter; handles file not found, read/write errors; tests pass, including error cases.
    2.  **Tool: `replace_text_in_note(path, find, replace, count=0)`**
        *   **Implementation:** `utils/vault_writer.py`. Basic string/regex replacement on note content (ensure frontmatter is preserved/handled). `count=0` means replace all.
        *   **Acceptance:** Replaces text correctly; respects count; handles frontmatter; handles file not found, read/write errors; tests pass, including error cases.
    3.  **Tool: `search_notes_by_metadata_field(key, value)`**
        *   **Implementation:** `utils/vault_search.py`. Iterate notes, parse metadata, check for key-value match.
        *   **Acceptance:** Returns notes matching specific metadata field; handles errors during metadata parsing gracefully (e.g., skips note, logs warning); tests pass.
    4.  **Tool: `get_local_graph(path)`**
        *   **Implementation:** `utils/vault_reader.py` (or similar). Combine results of `get_outgoing_links` and `get_backlinks`.
        *   **Acceptance:** Returns combined list/structure of incoming/outgoing links; handles errors from underlying link/backlink functions; tests pass.
    5.  **Tool: `append_to_note_by_metadata(key, value, content)`**
        *   **Implementation:** `utils/vault_writer.py`. Combine `search_notes_by_metadata_field` and `append_to_note`. Define behavior for multiple matches (e.g., append to all, error, return list and require user selection via path).
        *   **Acceptance:** Appends content to notes matching metadata; handles multiple matches as defined; handles search errors and underlying append errors; tests pass, including error cases.

*   **Dependencies:** Phase 1 (for metadata access).

---

## Phase 5: Complex Features & Future Enhancements

*   **Goal:** Implement more complex features requiring significant parsing or structural awareness, with comprehensive error handling.
*   **Components:**
    1.  **Tool: `list_vault_structure(path='/')`**
        *   **Implementation:** `utils/vault_reader.py`. Recursive directory traversal. Design clear output format (e.g., nested JSON with 'type': 'folder'/'note').
        *   **Acceptance:** Returns accurate vault structure; handles large vaults reasonably; handles permission errors during traversal gracefully (e.g., skips inaccessible directories, logs warnings); tests pass.
    2.  **Tool: `replace_in_section(path, heading, find, replace)`** (Potentially revisit `patch_note_section` if this is preferred)
        *   **Implementation:** Enhance Phase 3 section logic. Requires advanced Markdown parsing (beyond regex) within the identified section to *ignore* code blocks/fences during the find/replace. High complexity.
        *   **Acceptance:** Replaces text within section *only*, reliably skipping code blocks; handles advanced parsing errors, file I/O errors; tests pass for complex cases, including error handling.
    3.  **Tool: `split_note(path, criteria)`**
        *   **Implementation:** `utils/refactor.py` (new module likely needed). Requires robust parsing based on `criteria` (e.g., heading level), file creation logic (naming conventions needed), content allocation, and defined handling for frontmatter/linking/original note status. High complexity.
        *   **Acceptance:** Splits note according to defined criteria and handling rules. **Requires detailed specification of `criteria` options, naming strategy, frontmatter/link handling, and original note disposition before implementation.** Handles parsing errors, file naming conflicts, file creation errors, I/O errors. Tests cover various splitting scenarios and error conditions.

---

## Deferred / Re-evaluate

*   **`move_item` / `rename_item`:** Basic implementation (no link updates) could be added to Phase 4/5 if deemed valuable. Reliable link updating is likely infeasible and deferred indefinitely.
*   **Plugin Integrations:** Requires significant architectural changes (e.g., companion Obsidian plugin) or is likely infeasible externally. Deferred indefinitely / removed from this server's direct roadmap.
*   **Advanced Template Variables:** Add more substitutions (`{{TITLE}}`, custom vars) post-Phase 2 as needed.
