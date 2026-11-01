"""
The Artifacts screen: what will be parsed.
A search field above two cards: the categories on the left, the artifacts of the category
chosen on the right.
"""

import tkinter as tk
from tkinter import ttk

from PIL import ImageTk

from leapp_functions.app.artifact_list import group_by_category, toggle
from leapp_functions.app.gui import images, themes
from leapp_functions.app.gui.custom_widgets import (GAP, SIDE_WIDTH, Card, Field, LabeledEntry,
                                                    show_example)

SEARCH_EXAMPLE = "Search an artifact or a category"
COUNT_WIDTH = 64


class CategoryTree(tk.Frame):
    """ The categories: a box that selects or unselects all of its artifacts, its
    name, and how many of its artifacts are selected out of how many it holds. A category with
    none selected is greyed. A click on the name chooses the category. """

    def __init__(self, parent, app, background):
        colors = app.colors
        super().__init__(parent, bg=background)
        self.state = app.app_state
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, columns=("count",), show="tree", selectmode="browse",
                                 style="Card.Treeview")
        self.tree.column("#0", width=1, stretch=True)
        self.tree.column("count", anchor="e", width=COUNT_WIDTH, stretch=False)
        self.tree.tag_configure("none", foreground=colors.text_secondary)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview,
                                  style="Card.Vertical.TScrollbar")
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.tree.configure(yscrollcommand=scrollbar.set)

        box_colors = themes.check_box_colors(colors)
        off, on = box_colors["off"], box_colors["on"]
        self.boxes = {state: ImageTk.PhotoImage(images.check_box_image(
            themes.CHECK_BOX, box, themes.CHECK_BOX_GAP, mark), master=self)
            for state, box, mark in (("off", off, "check"), ("on", on, "check"),
                                     ("partial", on, "minus"))}

        self.groups = group_by_category(self.state.artifacts.listed)
        for category in self.groups:
            self.tree.insert("", "end", iid=category, text=category)
            self.refresh_row(category)
        first = next(iter(self.groups), None)
        if first is not None:
            self.tree.selection_set(first)
            self.tree.focus(first)

        self.tree.bind("<Button-1>", self.click)
        self.tree.bind("<space>", lambda _event: self.toggle(self.tree.focus()))

    def refresh_row(self, category):
        """ Show how many artifacts of a category are selected. """
        names = self.groups[category]
        chosen = len(self.state.artifacts.selected.intersection(names))
        box = "off" if not chosen else "on" if chosen == len(names) else "partial"
        self.tree.item(category, image=self.boxes[box], values=(f"{chosen}/{len(names)}",),
                       tags=() if chosen else ("none",))

    def click(self, event):
        """ A click on a box selects or unselects the artifacts of its category. """
        if self.tree.identify_element(event.x, event.y) != "image":
            return None
        self.toggle(self.tree.identify_row(event.y))
        return "break"

    def toggle(self, category):
        """ Select all the artifacts of a category, or none of them if they all are. """
        if not category:
            return
        toggle(self.groups[category], self.state.artifacts.selected)
        self.refresh_row(category)
        self.state.on_change()


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
        CategoryTree(self.categories.body, app, self.categories.background).pack(
            fill="both", expand=True)
        self.artifacts = Card(self, app, "ARTIFACTS")
        self.artifacts.grid(row=1, column=1, sticky="nsew", padx=(GAP, 0))

    def focus_search(self):
        """ Put the cursor in the search field: Ctrl+F """
        self.entry.focus_set()
