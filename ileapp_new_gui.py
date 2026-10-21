"""
The new LEAPPs GUI --> Work in progress.
"""

import tkinter as tk

from leapp_functions import leapp
from leapp_functions.app.gui import themes
from leapp_functions.app.gui.banner import Banner


class MainWindow(tk.Tk):
    """ The main Window """

    def __init__(self):
        super().__init__()
        self.title(f"{leapp.name} version {leapp.version}")
        self.minsize(900, 700)

        self.appearance = themes.Appearance(leapp.theme)

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
        self.banner = Banner(self, self)
        self.banner.pack(fill="x")


if __name__ == "__main__":
    MainWindow().mainloop()
