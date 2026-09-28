import pytest

from obsidian_mcp_server.utils import vault_reader, vault_writer, vault_search
from obsidian_mcp_server.utils.exceptions import MetadataError
from obsidian_mcp_server.utils.frontmatter import split_frontmatter


def test_horizontal_rules_are_not_frontmatter(vault):
    original = "---\nIntro paragraph\n---\nBody text"
    (vault / "hr.md").write_text(original)
    assert vault_reader.get_note_metadata("hr.md") == {}
    vault_writer.update_metadata("hr.md", {"a": 1}, backup=False)
    assert (vault / "hr.md").read_text() == "---\na: 1\n---\n" + original


def test_dashes_inside_value_do_not_split(vault):
    (vault / "d.md").write_text("---\ntitle: a---b\nz: 1\n---\nBody")
    assert vault_reader.get_note_metadata("d.md") == {"title": "a---b", "z": 1}
    vault_writer.update_metadata("d.md", {"a": 1}, backup=False)
    assert (vault / "d.md").read_text() == "---\ntitle: a---b\nz: 1\na: 1\n---\nBody"


def test_update_preserves_body_and_key_order(vault):
    body = "\n\n  indented first line\n---\nnot frontmatter: x\n---\n"
    (vault / "o.md").write_text("---\nz: 1\na: 2\n---\n" + body)
    vault_writer.update_metadata("o.md", {"a": 3}, backup=False)
    assert (vault / "o.md").read_text() == "---\nz: 1\na: 3\n---\n" + body


def test_invalid_yaml_is_not_discarded(vault):
    original = "---\nkey: [unclosed\n---\nBody"
    (vault / "bad.md").write_text(original)
    with pytest.raises(MetadataError):
        vault_writer.update_metadata("bad.md", {"a": 1}, backup=False)
    assert (vault / "bad.md").read_text() == original


def test_note_without_frontmatter_gets_block_prepended(vault):
    (vault / "p.md").write_text("Just text")
    vault_writer.update_metadata("p.md", {"tags": ["x"]}, backup=False)
    assert vault_reader.get_note_metadata("p.md") == {"tags": ["x"]}
    assert (vault / "p.md").read_text().endswith("---\nJust text")


def test_metadata_search_and_tags_use_same_parser(vault):
    (vault / "a.md").write_text("---\ntitle: a---b\ntags: [one]\n---\n#two")
    (vault / "b.md").write_text("---\nIntro\n---\n#three")
    assert vault_search.search_notes_metadata("a---b") == ["a.md"]
    assert vault_reader.get_all_tags() == ["one", "three", "two"]


@pytest.mark.parametrize("content", ["----\nx\n----\n", "--- \nx: 1\n---", "---\r\nx: 1\r\n---\r\nb"])
def test_delimiter_edge_cases(content):
    metadata, _, body = split_frontmatter(content)
    if content.startswith("----"):
        assert metadata is None and body == content
    else:
        assert metadata == {"x": 1}


def test_empty_frontmatter_block():
    assert split_frontmatter("---\n---\nbody") == ({}, "", "body")
