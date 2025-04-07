"""Custom exceptions for Obsidian MCP Server utilities."""

class VaultError(Exception):
    """Base class for errors related to vault operations."""
    pass

class NoteNotFoundError(VaultError):
    """Raised when a specified note is not found."""
    pass

class InvalidPathError(VaultError):
    """Raised when a path is invalid or outside the vault."""
    pass

class MetadataError(VaultError):
    """Raised during errors parsing or manipulating note metadata."""
    pass

class BackupError(VaultError):
    """Raised when creating a backup fails."""
    pass

class NoteCreationError(VaultError):
    """Raised when creating a note fails (e.g., already exists)."""
    pass 