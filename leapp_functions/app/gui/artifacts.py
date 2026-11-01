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
DETAILS = (("module", "Module"), ("name", "Artifact"))


def scrolled_tree(frame, columns):
    """ A Treeview with its scroll bar on the right. """
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    tree = ttk.Treeview(frame, columns=columns, show="tree", selectmode="browse",
                        style="Card.Treeview")
    tree.column("#0", width=1, stretch=True)
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview,
                              style="Card.Vertical.TScrollbar")
    scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
    tree.configure(yscrollcommand=scrollbar.set)
    return tree


def box_pictures(colors, master):
    """ The box in its three states: "off", "on" and "partial". """
    box_colors = themes.check_box_colors(colors)
    off, on = box_colors["off"], box_colors["on"]
    return {state: ImageTk.PhotoImage(images.check_box_image(
        themes.CHECK_BOX, box, themes.CHECK_BOX_GAP, mark), master=master)
        for state, box, mark in (("off", off, "check"), ("on", on, "check"),
                                 ("partial", on, "minus"))}


def bind_boxes(tree, on_box):
    """ A click on the box of a row, or Space on the row with the focus, calls on_box(row).
    A click anywhere else shows the choosen row. """
    def click(event):
        if tree.identify_element(event.x, event.y) != "image":
            return None
        on_box(tree.identify_row(event.y))
        return "break"

    tree.bind("<Button-1>", click)
    tree.bind("<space>", lambda _event: on_box(tree.focus()))


class CategoryTree(tk.Frame):
    """ The categories: a box that selects or unselects all of its artifacts, its
    name, and how many of its artifacts are selected out of how many it holds. A category with
    none selected is greyed. A click on the name chooses the category. """

    def __init__(self, parent, app, background, on_toggle):
        super().__init__(parent, bg=background)
        self.state = app.app_state
        self.on_toggle = on_toggle
        self.tree = scrolled_tree(self, ("count",))
        self.tree.column("count", anchor="e", width=COUNT_WIDTH, stretch=False)
        self.tree.tag_configure("none", foreground=app.colors.text_secondary)
        self.boxes = box_pictures(app.colors, self)

        self.groups = group_by_category(self.state.artifacts.listed)
        for category in self.groups:
            self.tree.insert("", "end", iid=category, text=category)
            self.refresh_row(category)
        first = next(iter(self.groups), None)
        if first is not None:
            self.tree.selection_set(first)
            self.tree.focus(first)
        bind_boxes(self.tree, self.toggle)

    def chosen(self):
        """ The category chosen. """
        selection = self.tree.selection()
        return selection[0] if selection else ""

    def refresh_row(self, category):
        """ Show how many artifacts of a category are selected. """
        names = self.groups[category]
        chosen = len(self.state.artifacts.selected.intersection(names))
        box = "off" if not chosen else "on" if chosen == len(names) else "partial"
        self.tree.item(category, image=self.boxes[box], values=(f"{chosen}/{len(names)}",),
                       tags=() if chosen else ("none",))

    def toggle(self, category):
        """ Select all the artifacts of a category, or none of them if they all are. """
        if not category:
            return
        toggle(self.groups[category], self.state.artifacts.selected)
        self.on_toggle(category)


class ArtifactTree(tk.Frame):
    """ The artifacts of a category: a box that selects or unselects it and its title, greyed
    when it is not selected. Under the list, the details of the artifact chosen. """

    def __init__(self, parent, app, background, on_toggle):
        colors = app.colors
        super().__init__(parent, bg=background)
        self.state = app.app_state
        self.on_toggle = on_toggle
        self.shown = {}  # the artifacts in the list, by name

        rows = tk.Frame(self, bg=background)
        rows.pack(fill="both", expand=True)
        self.tree = scrolled_tree(rows, ())
        self.tree.tag_configure("none", foreground=colors.text_secondary)
        self.boxes = box_pictures(colors, self)
        bind_boxes(self.tree, self.toggle)
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self.show_details())

        details = tk.Frame(self, bg=background)
        details.pack(fill="x", pady=(10, 0))
        details.columnconfigure(1, weight=1)
        tk.Frame(details, height=1, bg=colors.line).grid(row=0, column=0, columnspan=2,
                                                         sticky="ew", pady=(0, 8))
        self.details = {}
        for row, (key, text) in enumerate(DETAILS, start=1):
            tk.Label(details, text=text, anchor="w", bg=background, fg=colors.text_secondary,
                     font=themes.sans(11)).grid(row=row, column=0, sticky="w", padx=(0, 16))
            self.details[key] = tk.Label(details, anchor="w", width=1, bg=background,
                                         fg=colors.text_primary, font=themes.mono(12))
            self.details[key].grid(row=row, column=1, sticky="ew")

    def show(self, category):
        """ List the artifacts of a category, and choose the first one. """
        self.tree.delete(*self.tree.get_children())
        self.shown = {artifact.name: artifact for artifact in self.state.artifacts.listed
                      if artifact.category == category}
        for name, artifact in self.shown.items():
            self.tree.insert("", "end", iid=name, text=artifact.title)
        self.refresh_rows()
        first = next(iter(self.shown), None)
        if first is not None:
            self.tree.selection_set(first)
            self.tree.focus(first)
            self.tree.see(first)
        self.show_details()

    def refresh_rows(self):
        """ Show which artifacts of the list are selected. """
        selected = self.state.artifacts.selected
        for name in self.shown:
            on = name in selected
            self.tree.item(name, image=self.boxes["on" if on else "off"],
                           tags=() if on else ("none",))

    def show_details(self):
        """ Show the module and the name of the artifact chosen. """
        selection = self.tree.selection()
        artifact = self.shown.get(selection[0]) if selection else None
        values = {"module": f"{artifact.module}.py", "name": artifact.name} if artifact else {}
        for key, label in self.details.items():
            label.configure(text=values.get(key, ""))

    def toggle(self, name):
        """ Select an artifact, or unselect it if it is selected. """
        if not name:
            return
        toggle([name], self.state.artifacts.selected)
        self.on_toggle(self.shown[name].category)


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

        categories = Card(self, app, "CATEGORIES")
        categories.grid(row=1, column=0, sticky="nsew")
        self.category_list = CategoryTree(categories.body, app, categories.background,
                                          self.toggled)
        self.category_list.pack(fill="both", expand=True)

        artifacts = Card(self, app, "ARTIFACTS")
        artifacts.grid(row=1, column=1, sticky="nsew", padx=(GAP, 0))
        self.artifact_list = ArtifactTree(artifacts.body, app, artifacts.background, self.toggled)
        self.artifact_list.pack(fill="both", expand=True)

        self.category_list.tree.bind("<<TreeviewSelect>>", lambda _event: self.artifact_list.show(
            self.category_list.chosen()))
        self.artifact_list.show(self.category_list.chosen())

    def toggled(self, category):
        """ Artifacts of a category were selected or unselected. """
        self.category_list.refresh_row(category)
        self.artifact_list.refresh_rows()
        self.app.app_state.on_change()

    def focus_search(self):
        """ Put the cursor in the search field: Ctrl+F """
        self.entry.focus_set()
