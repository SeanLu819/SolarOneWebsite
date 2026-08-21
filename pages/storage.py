"""Custom storage backends.

OverwriteStorage: replaces Django's default "append hash suffix" behavior
with direct file overwrite. Useful when you want predictable file paths
and don't need versioned filenames.
"""
import os
from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):
    """FileSystemStorage that overwrites existing files instead of adding a hash suffix.

    Django's default FileSystemStorage.get_available_name() appends a 7-char
    random hash when a file with the same name exists. This storage instead
    deletes the old file before saving the new one, keeping filenames clean
    and predictable.
    """

    def get_available_name(self, name, max_length=None):
        """Return the name without modification — same name = overwrite."""
        # If the file already exists, delete it first so save() writes fresh
        if self.exists(name):
            try:
                self.delete(name)
            except Exception:
                pass
        return name
