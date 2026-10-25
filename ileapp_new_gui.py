"""
The new LEAPPs GUI --> Work in progress.
"""

import sys
import tkinter as tk
from tkinter import messagebox

from leapp_functions import leapp
from leapp_functions.app.gui import themes, images
from leapp_functions.app.gui.banner import Banner


class MainWindow(tk.Tk):
    """ The main Window """

    def __init__(self):
        super().__init__()
        self.title(f"{leapp.name} version {leapp.version}")
        self.icon = images.load("icon.png")
        self.iconphoto(True, self.icon)
        self.minsize(900, 700)

        self.appearance = themes.Appearance(leapp.theme)

        # Settings
        if sys.platform == "darwin":
            # On macOS: Settings item in the application menu and ⌘,
            self.createcommand("::tk::mac::ShowPreferences", self.open_settings)
        else:
            # Other platforms: Ctrl,
            self.bind_all("<Control-comma>", lambda _event: self.open_settings())

        self.banner = None
        self.page = None
        self.steps = None
        self.screen = None
        self.action_bar = None

        self.build()

    @property
    def colors(self):
        """The palette in use"""
        return self.appearance.colors

    def build(self):
        """ Build or replace every widget using the current palette """
        for widget in (self.banner, self.page):
            if widget is not None:
                widget.destroy()
        self.configure(bg=self.colors.main_bg)
        if sys.platform == "darwin":
            appearance = "darkaqua" if self.appearance.is_dark else "aqua"
            try:
                self.tk.call("::tk::unsupported::MacWindowStyle", "appearance", self, appearance)
            except tk.TclError:
                pass  # Tk before 8.6.10 has no such setting

        self.banner = Banner(self, self)
        self.banner.pack(fill="x")

    def open_settings(self):
        """The Settings window, not built yet."""
        messagebox.showinfo("Settings", "The Settings window is not built yet.", parent=self)


if __name__ == "__main__":
    MainWindow().mainloop()
