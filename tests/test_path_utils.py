"""Tests for vault path-containment (obsidian_mcp_server.utils.path_utils)."""

import os
import tempfile
import unittest

from obsidian_mcp_server.utils.path_utils import is_path_within_vault


class IsPathWithinVaultTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.parent = self._tmp.name
        self.vault = os.path.join(self.parent, "vault")
        os.makedirs(self.vault)

    def tearDown(self):
        self._tmp.cleanup()

    def _join(self, rel):
        # Mirrors how the callers build paths: os.path.join(VAULT_PATH, rel).
        return os.path.join(self.vault, rel)

    def test_vault_root_is_inside(self):
        self.assertTrue(is_path_within_vault(self.vault, self.vault))

    def test_direct_child_is_inside(self):
        self.assertTrue(is_path_within_vault(self._join("note.md"), self.vault))

    def test_nested_child_is_inside(self):
        self.assertTrue(
            is_path_within_vault(self._join("sub/dir/note.md"), self.vault)
        )

    def test_parent_traversal_is_rejected(self):
        self.assertFalse(
            is_path_within_vault(self._join("../../etc/passwd"), self.vault)
        )

    def test_sibling_prefix_bypass_is_rejected(self):
        # Regression: "/parent/vault-private" shares the string prefix of
        # "/parent/vault" and slipped past the old startswith() check.
        os.makedirs(os.path.join(self.parent, "vault-private"))
        self.assertFalse(
            is_path_within_vault(
                self._join("../vault-private/secret.md"), self.vault
            )
        )

    def test_symlink_escape_is_rejected(self):
        outside = os.path.join(self.parent, "outside")
        os.makedirs(outside)
        link = os.path.join(self.vault, "escape")
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not supported on this platform")
        self.assertFalse(
            is_path_within_vault(os.path.join(link, "secret.md"), self.vault)
        )


if __name__ == "__main__":
    unittest.main()
