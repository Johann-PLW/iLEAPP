"""
Dark and light palettes holding the same colour roles.
The colours are stored in the "theme" entry of data/leapp_config.json, one file
for each LEAPP, so that this module can stay the same in all of them.
"""

import re
import sys

HEX_COLOUR = re.compile(r"#[0-9A-Fa-f]{6}")
ROLES = frozenset((
    "banner_bg",  # banner background color, identical in both dark and light theme
    "main_bg",  # main window background color
    "text_primary",
    "text_secondary",
    "line",  # The line between the steps
    "progress"  # The line to indicate the progression of valid steps
))


def palette(theme, name):
    """
    Check roles: an extra or a missing role, a value that is not
    #RRGGBB is refused with a ValueError that names it.
    Args:
        theme (namedtuple): The "theme" entry of data/leapp_config.json file,
                            as leapp_functions builds it.
        name (str): "dark" or "light"
    Returns:
        namedtuple: The "dark" or the "light" namedtuple in the "theme" entry
                    of data/leapp_config.json file.

    """
    values = getattr(theme, name, None)
    if not hasattr(values, "_fields"):
        raise ValueError(f"no theme.{name} section")
    missing, unknown = sorted(ROLES - set(values._fields)), sorted(set(values._fields) - ROLES)
    if missing or unknown:
        raise ValueError(f"theme.{name} lacks {missing} and has unknown {unknown}")
    for role, value in zip(values._fields, values):
        if not (isinstance(value, str) and HEX_COLOUR.fullmatch(value)):
            raise ValueError(f"theme.{name}.{role} is {value!r}, not a #RRGGBB colour")
    return values


class Appearance:
    """The two palettes of the window, and the one in use."""

    def __init__(self, config):
        self.dark = palette(config, "dark")
        self.light = palette(config, "light")
        self.colors = self.dark

    @property
    def is_dark(self):
        """Return True if the palette in use is the dark one, otherwise False."""
        return self.colors is self.dark

    def toggle(self):
        """Switch to the other palette."""
        self.colors = self.light if self.is_dark else self.dark


if sys.platform == "darwin":
    SANS, MONO = ".AppleSystemUIFont", "Menlo"
elif sys.platform == "win32":
    SANS, MONO = "Segoe UI", "Consolas"
else:
    SANS, MONO = "DejaVu Sans", "DejaVu Sans Mono"


def sans(size, weight="normal"):
    """ The normal font. """
    return (SANS, -size, weight)


def mono(size, weight="normal"):
    """ The monospaced font. """
    return (MONO, -size, weight)
