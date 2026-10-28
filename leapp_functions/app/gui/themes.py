"""
Dark and light palettes holding the same colour roles.
The colours are stored in the "theme" entry of data/leapp_config.json, one file
for each LEAPP, so that this module can stay the same in all of them.
"""

import re
import sys

HEX_COLOUR = re.compile(r"#[0-9A-Fa-f]{6}")
ROLES = frozenset((
    "border",  # The border of a card and of an input with the focus, the line above the status bar
    "card",
    "header_bg",  # The header background color, identical in both dark and light theme
    "input",
    "line",  # The line between the steps
    "main_bg",  # The main window background color
    "progress",  # The line to indicate the progression of valid steps
    "red_text",
    "text_legend",
    "text_primary",
    "text_secondary",
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


def apply_styles(style, colors):
    """Give the ttk buttons the colours of a palette.

    Primary is the outlined button: the window's background and the text in the header's
    colour, and under the pointer the text in the primary colour. Filled is the button that
    moves on: the header's colour for its background and the window's for its text, and under
    the pointer the text in the primary colour.
    """
    for name, background, foreground, disabled, hover, hover_text in (
            ("Primary", colors.main_bg, colors.header_bg, (colors.main_bg, colors.text_legend),
             colors.main_bg, colors.text_primary),
            ("Filled", colors.header_bg, colors.main_bg, (colors.line, colors.main_bg),
             colors.header_bg, colors.text_primary)):
        disabled_background, disabled_text = disabled
        style.configure(f"{name}.TButton", background=background, foreground=foreground,
                        bordercolor=background, lightcolor=background, darkcolor=background,
                        font=sans(12, "bold"), padding=(18, 7), borderwidth=0, relief="flat",
                        focuscolor=background)
        # The dotted ring of the focus is drawn in the colour of the button so that it does
        # not show
        states = [("disabled", disabled_background), ("pressed", hover), ("active", hover)]
        style.map(f"{name}.TButton",
                  background=states,
                  foreground=[("disabled", disabled_text), ("pressed", hover_text),
                              ("active", hover_text)],
                  bordercolor=states, lightcolor=states, darkcolor=states, focuscolor=states)
