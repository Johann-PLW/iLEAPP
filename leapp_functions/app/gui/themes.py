"""
Dark and light palettes holding the same colour roles.
The colours are stored in the "theme" entry of data/leapp_config.json, one file
for each LEAPP, so that this module can stay the same in all of them.
"""

import re
import sys

from PIL import ImageTk

from leapp_functions.app.gui import images

HEX_COLOUR = re.compile(r"#[0-9A-Fa-f]{6}")

CHECK_BOX = 16
CHECK_BOX_GAP = 8
CHECK_BOX_PICTURES = {}
ROLES = frozenset((
    "border",  # A card's border, an input's border with the focus, the line above the status bar
    "button_border",  # The border of a quiet button and of a button in a card
    "card_accent",  # The background of a card that sums up (report preview, detected), a shade apart from card_bg
    "card_bg",  # The background of a card and of its labels
    "header_bg",  # The header background color, identical in both themes, the border of an accent card
    "input_bg",  # The background of an input
    "line",  # The lines between the steps, an input's border, the fill of a button in a card
    "main_bg",  # The main window background color
    "progress",  # The line of the steps, from the first one to the one on show
    "text_error",  # A problem, the subtitle of the status bar when Next is blocked: red in every LEAPP
    "text_legend",  # The subtitle of the status bar, the text of a button that cannot be used
    "text_primary",  # The text of titles (cards too), inputs and buttons, the icon of a step on show or done
    "text_secondary",  # The label above an input, the icon and title of a step not reached
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
    """ The two palettes of the window, and the one in use. """

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
    """ Give the ttk buttons and check boxes the colours of a palette. """
    for name, background, foreground, disabled, hover, hover_text in (
            ("Primary", colors.main_bg, colors.header_bg, (colors.main_bg, colors.text_legend),
             colors.main_bg, colors.text_primary),
            ("Filled", colors.header_bg, colors.main_bg, (colors.line, colors.main_bg),
             colors.header_bg, colors.text_primary),
            ("Quiet", colors.main_bg, colors.text_primary, (colors.main_bg, colors.text_legend),
             colors.line, colors.text_primary),
            ("Field", colors.line, colors.text_primary, (colors.line, colors.text_legend),
             colors.border, colors.text_primary)):
        disabled_background, disabled_text = disabled
        style.configure(f"{name}.TButton", background=background, foreground=foreground,
                        bordercolor=background, lightcolor=background, darkcolor=background,
                        font=sans(12, "bold"), padding=(18, 7), borderwidth=0, relief="flat",
                        focuscolor=background)
        states = [("disabled", disabled_background), ("pressed", hover), ("active", hover)]
        style.map(f"{name}.TButton",
                  background=states,
                  foreground=[("disabled", disabled_text), ("pressed", hover_text),
                              ("active", hover_text)],
                  bordercolor=states, lightcolor=states, darkcolor=states, focuscolor=states)
    style.configure("Field.TButton", padding=(18, 3, 18, 4))
    style_check_box(style, colors)


def style_check_box(style, colors):
    """ A check box in a card. """
    pictures = {state: images.check_box_image(CHECK_BOX, box_colors, CHECK_BOX_GAP)
                for state, box_colors in (
                    ("off", (colors.input_bg, colors.border, None)),
                    ("on", (colors.input_bg, colors.border, colors.text_primary)),
                    ("disabled", (colors.card_bg, colors.line, None)))}
    if "Tick.indicator" in style.element_names():
        for state, picture in pictures.items():
            CHECK_BOX_PICTURES[state].paste(picture)
    else:
        for state, picture in pictures.items():
            CHECK_BOX_PICTURES[state] = ImageTk.PhotoImage(picture, master=style.master)
        style.element_create("Tick.indicator", "image", CHECK_BOX_PICTURES["off"],
                             ("disabled", CHECK_BOX_PICTURES["disabled"]),
                             ("selected", CHECK_BOX_PICTURES["on"]), sticky="")
    style.layout("Card.TCheckbutton", [("Checkbutton.padding", {"sticky": "nswe", "children": [
        ("Tick.indicator", {"side": "left", "sticky": ""}),
        ("Checkbutton.focus", {"side": "left", "sticky": "w",
                               "children": [("Checkbutton.label", {"sticky": "nswe"})]})]})])
    style.configure("Card.TCheckbutton", background=colors.card_bg, foreground=colors.text_primary,
                    font=sans(12), focuscolor=colors.card_bg)
    style.map("Card.TCheckbutton", background=[("active", colors.card_bg)],
              foreground=[("disabled", colors.text_legend)])
