"""
The Artifacts screen: what will be parsed.
A search field above two cards: the categories on the left, the artifacts of the category
chosen on the right.
"""

import tkinter as tk

from leapp_functions.app.gui.custom_widgets import (GAP, SIDE_WIDTH, Card, Field, LabeledEntry,
                                                    show_example)

SEARCH_EXAMPLE = "Search an artifact or a category"


class ArtifactsScreen(tk.Frame):
    """ The search field, the categories and the artifacts. """

    def __init__(self, parent, app):
        colors = app.colors
        super().__init__(parent, bg=colors.main_bg)
        self.app = app

        self.columnconfigure(0, minsize=SIDE_WIDTH)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self.search = tk.StringVar()
        field = LabeledEntry(self, app, Field("", self.search), background=colors.main_bg)
        field.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, GAP))
        show_example(field, app, self.search, SEARCH_EXAMPLE)
        self.entry = field.entry

        self.categories = Card(self, app, "CATEGORIES")
        self.categories.grid(row=1, column=0, sticky="nsew")
        self.artifacts = Card(self, app, "ARTIFACTS")
        self.artifacts.grid(row=1, column=1, sticky="nsew", padx=(GAP, 0))

    def focus_search(self):
        """ Put the cursor in the search field: Ctrl+F """
        self.entry.focus_set()
