"""
The Artifacts screen: what will be parsed.
A search field above two cards: the categories on the left, the artifacts of the category
chosen on the right.
"""

import tkinter as tk
from tkinter import ttk

from PIL import ImageTk

from leapp_functions.app.artifact_list import group_by_category, search, toggle
from leapp_functions.app.gui import images, themes
from leapp_functions.app.gui.custom_widgets import (GAP, SIDE_WIDTH, Card, Field, LabeledEntry,
                                                    OutlineButton, show_example)

SEARCH_EXAMPLE = "Search an artifact or a category"
COUNT_WIDTH = 64
DETAILS = (("module", "Module"), ("name", "Artifact"))
ROW = "artifact:"
HEADER = "category:"


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


def category_of(row):
    """ The category of a category row, or None for any other row. """
    return row[len(HEADER):] if row.startswith(HEADER) else None


def choose(tree, row):
    """ Choose a row and show it. """
    tree.selection_set(row)
    tree.focus(row)
    tree.see(row)


class CategoryTree(tk.Frame):
    """ The categories: a box that selects or unselects all of its artifacts, its
    name, and how many of its artifacts are selected out of how many it holds. A category with
    none selected is greyed. A click on the name chooses the category.
    While a search is on, only the categories found are listed, and their box and their count
    are about the artifacts found only. """

    def __init__(self, parent, app, background, on_toggle):
        super().__init__(parent, bg=background)
        self.state = app.app_state
        self.on_toggle = on_toggle
        self.tree = scrolled_tree(self, ("count",))
        self.tree.column("count", anchor="e", width=COUNT_WIDTH, stretch=False)
        self.tree.tag_configure("none", foreground=app.colors.text_secondary)
        self.boxes = box_pictures(app.colors, self)
        self.groups = {}
        bind_boxes(self.tree, self.toggle)

    def show(self, groups):
        """ List the categories, and keep the one chosen if it is still listed. """
        chosen = self.chosen()
        self.tree.delete(*self.tree.get_children())
        self.groups = groups
        for category in groups:
            self.tree.insert("", "end", iid=HEADER + category, text=category)
            self.refresh_row(category)
        if chosen not in groups:
            chosen = next(iter(groups), None)
        if chosen is not None:
            choose(self.tree, HEADER + chosen)

    def chosen(self):
        """ The category chosen. """
        selection = self.tree.selection()
        return category_of(selection[0]) if selection else None

    def refresh_row(self, category):
        """ Show how many artifacts of a category are selected. """
        names = self.groups[category]
        chosen = len(self.state.artifacts.selected.intersection(names))
        box = "off" if not chosen else "on" if chosen == len(names) else "partial"
        self.tree.item(HEADER + category, image=self.boxes[box], values=(f"{chosen}/{len(names)}",),
                       tags=() if chosen else ("none",))

    def refresh_rows(self):
        """ Show how many artifacts of each category are selected. """
        for category in self.groups:
            self.refresh_row(category)

    def toggle(self, row):
        """ Select all the artifacts of a category, or none of them if they all are. """
        category = category_of(row)
        if category is None:
            return
        toggle(self.groups[category], self.state.artifacts.selected)
        self.on_toggle(category)


class SearchBar(tk.Frame):
    """ Search over categories and artifacts. """

    def __init__(self, parent, app, background, on_all):
        super().__init__(parent, bg=background)
        self.found = tk.Label(self, anchor="w", bg=background, fg=app.colors.text_secondary,
                              font=themes.sans(11))
        self.found.pack(side="left", fill="x", expand=True)
        self.buttons = [OutlineButton(self, app, text=text, style="in_card",
                                      command=lambda select=select: on_all(select))
                        for text, select in (("All", True), ("None", False))]
        for button in reversed(self.buttons):
            button.pack(side="right", padx=(8, 0))

    def show(self, groups):
        """ Say how many artifacts and categories were found. """
        found = sum(len(names) for names in groups.values())
        if found:
            artifacts = "artifact" if found == 1 else "artifacts"
            categories = "category" if len(groups) == 1 else "categories"
            self.found.configure(text=f"{found} {artifacts} found in {len(groups)} {categories}")
        else:
            self.found.configure(text="No artifact found")
        for button in self.buttons:
            button.set_enabled(bool(found))


class ArtifactTree(tk.Frame):
    """ The artifacts of a category: a box that selects or unselects it and its title, greyed
    when it is not selected. Under the list, the details of the artifact chosen.
    While a search is on, the artifacts found are listed under the name of their category. """

    def __init__(self, parent, app, background, on_toggle):
        colors = app.colors
        super().__init__(parent, bg=background)
        self.state = app.app_state
        self.on_toggle = on_toggle
        self.by_name = {artifact.name: artifact for artifact in self.state.artifacts.listed}
        self.shown = {}  # the artifacts in the list, by row

        rows = tk.Frame(self, bg=background)
        rows.pack(fill="both", expand=True)
        self.tree = scrolled_tree(rows, ())
        self.tree.tag_configure("none", foreground=colors.text_secondary)
        self.tree.tag_configure("header", foreground=colors.text_secondary,
                                font=themes.sans(12, "bold"))
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

    def show(self, groups, found):
        """ List the artifacts of groups, and choose the first one.
        Args:
            groups (dict): the names of the artifacts to list, by category.
            found (bool): whether they were found by a search, which lists them under their
                category.
        """
        self.tree.delete(*self.tree.get_children())
        self.shown = {}
        for category, names in groups.items():
            parent = ""
            if found:
                parent = self.tree.insert("", "end", iid=HEADER + category, text=category,
                                          open=True, tags=("header",))
            for name in names:
                row = ROW + name
                self.shown[row] = self.by_name[name]
                self.tree.insert(parent, "end", iid=row, text=self.shown[row].title)
        self.refresh_rows()
        first = next(iter(self.shown), None)
        if first is not None:
            choose(self.tree, first)
        self.show_details()

    def reveal(self, category):
        """ Scroll the artifacts found so that those of a category come first, and choose the
        first one. """
        header = HEADER + category
        if not self.tree.exists(header):
            return
        headers = self.tree.get_children()
        rows = len(headers) + len(self.shown)
        before = 0
        for other in headers[:headers.index(header)]:
            before += 1 + len(self.tree.get_children(other))
        self.tree.yview_moveto(before / rows)
        first = self.tree.get_children(header)[0]
        self.tree.selection_set(first)
        self.tree.focus(first)

    def refresh_rows(self):
        """ Show which artifacts of the list are selected. """
        selected = self.state.artifacts.selected
        for row, artifact in self.shown.items():
            on = artifact.name in selected
            self.tree.item(row, image=self.boxes["on" if on else "off"],
                           tags=() if on else ("none",))

    def show_details(self):
        """ Show the module and the name of the artifact chosen. """
        selection = self.tree.selection()
        artifact = self.shown.get(selection[0]) if selection else None
        values = {"module": f"{artifact.module}.py", "name": artifact.name} if artifact else {}
        for key, label in self.details.items():
            label.configure(text=values.get(key, ""))

    def toggle(self, row):
        """ Select an artifact, or unselect it if it is selected. A category name has no box. """
        artifact = self.shown.get(row)
        if artifact is None:
            return
        toggle([artifact.name], self.state.artifacts.selected)
        self.on_toggle(artifact.category)


class ArtifactsScreen(tk.Frame):
    """ The search field, the categories and the artifacts. """

    def __init__(self, parent, app):
        colors = app.colors
        super().__init__(parent, bg=colors.main_bg)
        self.app = app
        self.groups = {}  # the names of the artifacts found, by category

        self.columnconfigure(0, minsize=SIDE_WIDTH)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self.search = tk.StringVar(value=app.app_state.artifacts.search)
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
        self.search_bar = SearchBar(artifacts.body, app, artifacts.background, self.select_found)
        self.artifact_list = ArtifactTree(artifacts.body, app, artifacts.background, self.toggled)
        self.artifact_list.pack(fill="both", expand=True)

        self.category_list.tree.bind("<<TreeviewSelect>>", lambda _event: self.category_chosen())
        trace = self.search.trace_add("write", lambda *_args: self.searched())
        self.bind("<Destroy>", lambda event: event.widget is self and self.search.trace_remove(
            "write", trace))
        self.searched()

    def searching(self):
        """ Whether a search is on. """
        return bool(self.search.get())

    def searched(self):
        """ The text searched changed: list what it finds. """
        state = self.app.app_state
        state.artifacts.search = self.search.get()
        self.groups = group_by_category(search(state.artifacts.listed, state.artifacts.search))
        self.category_list.show(self.groups)
        if self.searching():
            self.search_bar.show(self.groups)
            self.search_bar.pack(fill="x", pady=(0, 10), before=self.artifact_list)
            self.artifact_list.show(self.groups, found=True)
        else:
            self.search_bar.pack_forget()
            self.category_chosen()

    def category_chosen(self):
        """ A category was chosen: show its artifacts, or those found in it. """
        category = self.category_list.chosen()
        if category is None:
            return
        if self.searching():
            self.artifact_list.reveal(category)
        else:
            self.artifact_list.show({category: self.groups.get(category, [])}, found=False)

    def toggled(self, category):
        """ Artifacts of a category were selected or unselected. """
        self.category_list.refresh_row(category)
        self.artifact_list.refresh_rows()
        self.app.app_state.on_change()

    def select_found(self, select):
        """ Select every artifact found, or unselect them all: All and None. """
        selected = self.app.app_state.artifacts.selected
        for names in self.groups.values():
            if select:
                selected.update(names)
            else:
                selected.difference_update(names)
        self.category_list.refresh_rows()
        self.artifact_list.refresh_rows()
        self.app.app_state.on_change()

    def focus_search(self):
        """ Put the cursor in the search field: Ctrl+F """
        self.entry.focus_set()
