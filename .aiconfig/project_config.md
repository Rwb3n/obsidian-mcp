# Project Configuration (Long-Term Memory)

## Project Goal
Create a Model Context Protocol (MCP) server that allows authorized LLMs to interact with a user's Obsidian vault.

## Core Technologies
- Python
- FastAPI (Web Framework)
- modelcontextprotocol (Python SDK)
- PyYAML (for Frontmatter/Metadata)
- [Markdown/Frontmatter Library TBD]

## Key Coding Rules & Limitations
- Adhere to the [LLM Application Development Playbook](../../docs/guide.md).
- **CRITICAL:** All Python files MUST be limited to 200 lines.
- Prioritize safety: implement backups before modifying vault files.
- Follow MCP specifications using the official Python SDK.
- Vault path configuration: Initial: Hardcoded absolute path `D:\Documents\OBSIDIAN\OBSIDIAN - Copy`. Future: Allow relative paths/environment variable.

## Obsidian Configuration Assumptions (Initial Defaults)
- Daily Note Location: `/` (Vault Root)
- Daily Note Format: `YYYY-MM-DD`
- Daily Note Template: `(None)` 