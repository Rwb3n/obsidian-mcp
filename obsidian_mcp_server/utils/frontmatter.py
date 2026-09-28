"""YAML frontmatter parsing shared by readers, writers and search."""

import re
import yaml

# Frontmatter must open on the first line and close on a line that is exactly '---'.
# A '---' inside a value (e.g. `title: a---b`) is therefore not a delimiter.
_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)(?:\r?\n)?^---[ \t]*(?:\r?\n|\Z)", re.DOTALL | re.MULTILINE)


def split_frontmatter(content):
    """Splits a note into (metadata, frontmatter_text, body).

    Returns (None, None, content) when the note has no frontmatter block, or when
    the block does not parse to a mapping (e.g. text between two horizontal
    rules), so callers never mistake note body for metadata.

    Raises:
        yaml.YAMLError: If a frontmatter block exists but is not valid YAML.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return None, None, content
    frontmatter_text = match.group(1)
    metadata = yaml.safe_load(frontmatter_text) if frontmatter_text.strip() else {}
    if not isinstance(metadata, dict):
        return None, None, content
    return metadata, frontmatter_text, content[match.end():]


def render_frontmatter(metadata):
    """Serialises metadata as a frontmatter block, preserving key order."""
    return "---\n" + yaml.safe_dump(metadata, allow_unicode=True, default_flow_style=False, sort_keys=False) + "---\n"
