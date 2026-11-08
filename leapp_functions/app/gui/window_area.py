"""
Where the window can be on the screen, which each system knows and says in its own way.
"""

import re
import sys
import time
import tkinter as tk

RESERVE = 100
ZOOM_TRIES = 50
SMALLEST_MAXIMIZED = 350
FRAME_POSITION = re.compile(r"\d+x\d+\+(-?\d+)\+(-?\d+)")


def frame_position(window):
    """ Where the window is, title bar included, or None if it is not told from the top left. """
    found = FRAME_POSITION.fullmatch(window.geometry())
    return (int(found[1]), int(found[2])) if found else None


def zoom(window, zoomed):
    """ Maximize the window or not. """
    before = window.winfo_height()
    if sys.platform.startswith("linux"):
        window.attributes("-zoomed", zoomed)
    else:
        window.state("zoomed" if zoomed else "normal")
    for _try in range(ZOOM_TRIES):
        window.update()
        if window.winfo_height() != before:
            return True
        time.sleep(0.01)
    return False


def measure(window):
    """ Where a window can be on the screen the mouse pointer is on. """
    area = (0, 0, window.winfo_screenwidth(), window.winfo_screenheight() - RESERVE)
    try:
        window.attributes("-alpha", 0)
        pointer_x, pointer_y = window.winfo_pointerxy()
        window.geometry(f"1x1+{pointer_x}+{pointer_y}")
        window.update()
        if zoom(window, True):
            if window.winfo_height() > SMALLEST_MAXIMIZED:
                x, y = frame_position(window) or (0, 0)
                area = (x, y, window.winfo_width(), window.winfo_height())
            zoom(window, False)
    except tk.TclError:
        pass  # a system that cannot do this: the screen less what is left to it
    window.withdraw()
    window.attributes("-alpha", 1)
    return area


def place(window, area, width, height):
    """ Give the window a size and centre it on the screen it was measured on. """
    left, top, room_width, room_height = area
    x = left + max(0, (room_width - width) // 2)
    y = top + max(0, (room_height - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
