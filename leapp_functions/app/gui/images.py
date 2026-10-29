"""
Images, read from the assets folder.
Tabler icons, glyphs of tabler-icons.ttf found in tabler-icons.css: https://tabler.io/icons lists them all.
"""

import base64
import io
import re
import sys
from functools import cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageTk

# From source, the root is the root of the repository.
# In a a build, PyInstaller unpacks it into the folder named by sys._MEIPASS.
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
ASSETS = ROOT / "assets"
ELEMENTS = ROOT / "scripts" / "_elements"
CSS_FILE = ELEMENTS / "tabler-icons.css"
FONT_FILE = ELEMENTS / "fonts" / "tabler-icons" / "tabler-icons.ttf"

# A rule of the CSS
RULE = re.compile(r'\.ti-([\w-]+):before\s*\{\s*content:\s*"\\([0-9a-f]+)"')

# The tick badge of an icon: its radius, its distance from the icon's centre (right and down)
# and the size of the tick inside it, in pixels
TICK_RADIUS = 8
TICK_OFFSET = 12
TICK_SIZE = 13
SMOOTHING = 4

DISC_MARK_SCALE = 1.5


def from_base64(encoded, width, height):
    """ The picture held by a base64 string, reduced to fit in a box of width by height pixels.
    Returns None when the string is not a picture. """
    try:
        picture = Image.open(io.BytesIO(base64.b64decode(encoded, validate=True)))
        picture.thumbnail((width, height))
        return ImageTk.PhotoImage(picture.convert("RGBA"))
    except (OSError, ValueError, Image.DecompressionBombError):
        return None


def load(name, height=None):
    """ Return the image from the image name, scaled to height pixels when a height is given. """
    image = Image.open(ASSETS / name)
    if height:
        width = round(image.width * height / image.height)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


@cache
def glyphs():
    """ Every icon name with its character in the font, read from the CSS once. """
    css = CSS_FILE.read_text(encoding="utf-8")
    return {name: chr(int(code, 16)) for name, code in RULE.findall(css)}


@cache
def font(size):
    """ The font at a size in pixels, opened once for each size. """
    return ImageFont.truetype(str(FONT_FILE), size)


@cache
def icon_image(name, size, color, margin=0, tick=None):
    """
    The icon, in a #RRGGBB colour, as a Pillow image on a transparent background.
    Args:
        name (str): Tabler icon name
        size (int): Icon size in pixels
        color (str): Hex color
        margin (int): Transparent pixels added around
        tick (None|str): Disc color, tick color
    """
    try:
        glyph = glyphs()[name]
    except KeyError:
        raise ValueError(f"There is no Tabler icon named {name!r}") from None
    side = size + 2 * margin
    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    ImageDraw.Draw(image).text((side / 2, side / 2), glyph, font=font(size), fill=color,
                               anchor="mm")
    if tick is None:
        return image

    disc_color, tick_color = tick
    centre = side / 2 + TICK_OFFSET

    def circle(radius):
        """ A mask of a smooth disc of this radius at the badge's place. """
        big = side * SMOOTHING
        mask = Image.new("L", (big, big), 0)
        box = [(centre - radius) * SMOOTHING, (centre - radius) * SMOOTHING,
               (centre + radius) * SMOOTHING, (centre + radius) * SMOOTHING]
        ImageDraw.Draw(mask).ellipse(box, fill=255)
        return mask.resize((side, side), Image.Resampling.LANCZOS)

    ring = circle(TICK_RADIUS + 2)
    image.putalpha(ImageChops.multiply(image.getchannel("A"), ImageChops.invert(ring)))

    # The disc, then the tick centred on it
    disc = Image.new("RGBA", (side, side), disc_color)
    disc.putalpha(circle(TICK_RADIUS))
    image = Image.alpha_composite(image, disc)
    mark = icon_image("check", TICK_SIZE, tick_color)
    image.alpha_composite(mark, (round(centre - TICK_SIZE / 2), round(centre - TICK_SIZE / 2)))
    return image


def load_icon(name, size, color, margin=0, tick=None):
    """ icon_image() as an image Tk can show. """
    return ImageTk.PhotoImage(icon_image(name, size, color, margin, tick))


@cache
def disc_icon_image(name, size, disc_color, mark_color):
    """ A glyph in a filled disc, as a Pillow image on a transparent background: a filled version of
    an outlined icon, which stays readable when small.
    Args:
        name (str): Tabler icon name of the glyph, such as "info-small"
        size (int): Diameter of the disc in pixels
        disc_color (str): Hex color of the disc
        mark_color (str): Hex color of the glyph
    """
    big = size * SMOOTHING
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse([0, 0, big - 1, big - 1], fill=disc_color)
    mark = icon_image(name, round(size * DISC_MARK_SCALE * SMOOTHING), mark_color)
    image.alpha_composite(mark, ((big - mark.width) // 2, (big - mark.height) // 2))
    return image.resize((size, size), Image.Resampling.LANCZOS)


def load_disc_icon(name, size, disc_color, mark_color):
    """ disc_icon_image() as an image Tk can show. """
    return ImageTk.PhotoImage(disc_icon_image(name, size, disc_color, mark_color))
