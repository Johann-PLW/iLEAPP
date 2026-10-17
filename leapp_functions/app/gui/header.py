""" The banner in the LEAPPs App's color """

import tkinter as tk


class Header(tk.Frame):
    """ Banner of the main window """
    def __init__(self, parent, app):
        super().__init__(parent, bg="#FC3E69", height=60)
        screen = app.screen
        print(screen)
