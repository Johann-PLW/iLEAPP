"""
The new LEAPPs GUI --> Work in progress.
"""

import tkinter as tk

from leapp_functions.app.gui.header import Header
from leapp_functions import leapp


class MainWindow(tk.Tk):
    """ The main Window """

    def __init__(self):
        super().__init__()
        self.title(f"{leapp.name} version {leapp.version}")
        self.minsize(900, 700)

        self.header = None
        self.page = None
        self.steps = None
        self.screen = None
        self.action_bar = None

        self.build()

    def build(self):
        """ Build or replace every widget using the current palette """
        for widget in (self.header, self.page):
            if widget is not None:
                widget.destroy()
        self.configure(bg="#0E0F13")
        self.header = Header(self, self)
        self.header.pack(fill="x")


if __name__ == "__main__":
    MainWindow().mainloop()
