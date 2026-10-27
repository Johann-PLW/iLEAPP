""" The header in the LEAPPs App's color """

import tkinter as tk
import webbrowser

from leapp_functions import leapp
from leapp_functions.app.gui import images


class Header(tk.Frame):
    """ Header of the main window """
    def __init__(self, parent, app):
        colors = self.colors = app.colors
        super().__init__(parent, bg=colors.header_bg)

        self.leapp_logo = images.load(f"{leapp.name}_logo.png")
        self.leapps_logo = images.load("leapps_logo.png", height=51)

        tk.Label(self, image=self.leapp_logo, bg=colors.header_bg).pack(
            side="left", padx=16, pady=8)
        tk.Frame(self, bg=colors.header_bg).pack(side="left", expand=True)
        leapps_link = tk.Label(self, image=self.leapps_logo, bg=colors.header_bg, cursor="target")
        leapps_link.pack(side="left", padx=16, pady=8)
        leapps_link.bind('<Button-1>', lambda _event: webbrowser.open_new_tab('https://leapps.org'))
