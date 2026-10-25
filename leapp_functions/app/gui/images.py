""" Images for the LEAPPs GUI, read from the assets folder. """

import sys
from pathlib import Path

from PIL import Image, ImageTk

# From source, assets/ is at the root of the repository.
# From a build, PyInstaller unpacks it into the folder named by sys._MEIPASS.
ASSETS = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3])) / "assets"


def load(name, height=None):
    """ The image assets/<name>, scaled to height pixels when a height is given. """
    image = Image.open(ASSETS / name)
    if height:
        width = round(image.width * height / image.height)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)
