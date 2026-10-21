""" The banner in the LEAPPs App's color """

import tkinter as tk


class Banner(tk.Frame):
    """ Banner of the main window """
    def __init__(self, parent, app):
        colors = self.colors = app.colors
        super().__init__(parent, bg=colors.banner_bg, height=60)
        screen = app.screen
        print(screen)
