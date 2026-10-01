# Security Policy

## Trust model

`obsidian-mcp` is a local MCP server that reads and writes files in a single
configured Obsidian vault. It is designed to run on `localhost` and be reached
only by an MCP client on the same machine.

- The **vault directory is the trust boundary.** Tools are expected to operate
  only on files inside the configured vault; paths that resolve outside it are
  rejected.
- The **tool caller (the MCP client / LLM) is untrusted input.** Note paths and
  content supplied to the tools are validated before use.
- Do **not** bind the server to a non-loopback address (e.g. `0.0.0.0`) on an
  untrusted network. Doing so exposes an unauthenticated read/write/delete API.

## Supported versions

Security fixes are applied to the latest release / the `main` branch. Older
versions are not maintained.

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** rather than opening a
public issue:

- Use GitHub's **"Report a vulnerability"** button under this repository's
  **Security** tab (Security Advisories), or
- Contact the maintainer directly through their GitHub profile.

Please include a description, affected version/commit, and steps to reproduce
or a proof of concept. We aim to acknowledge reports promptly and will
coordinate a fix and disclosure timeline with you.
