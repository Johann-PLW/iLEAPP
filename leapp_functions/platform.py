"""Platform-specific module for cross-platform path handling and compatibility."""

import sys
from pathlib import Path


def is_platform_windows():
    '''Returns True if running on Windows'''
    return sys.platform == 'win32'


def win_convert_to_long_path(path):
    """If it has a driver letter, convert a Path object to a Windows long path
    format to support paths longer than 260 characters.
    Args:
        path (Path): A pathlib.Path object to convert.
    Returns:
        Path: A new Path object prefixed with '\\\\?\\' for extended-length path support,
              if the path has a drive, otherwise returns the original path unchanged.
    """
    if path.drive:
        return Path(r"\\?\\" + path.as_posix().replace('/', '\\'))
    return path
