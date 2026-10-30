"""
The Source screen: the extraction to parse, where the keychain and the report go.
"""

import tkinter as tk
from tkinter import filedialog

from leapp_functions import leapp
from leapp_functions.app import history
from leapp_functions.app.gui.custom_widgets import (Caption, Card, Field, LabeledEntry,
                                                    OutlineButton, Tooltip, two_columns)
from scripts.raw_image import RAW_IMAGE_FILE_PATTERNS, RAW_IMAGE_LABEL, selection_text

FILE_TYPES = (("All supported files", "*.tar *.zip *.gz *.xz " + RAW_IMAGE_FILE_PATTERNS),
              ("tar file", "*.tar"), ("zip file", "*.zip"), ("gz file", "*.gz"),
              ("tar.xz file", "*.xz"), (RAW_IMAGE_LABEL, RAW_IMAGE_FILE_PATTERNS))


class SourceScreen(tk.Frame):
    """ The fields of the Source screen, which edit the variables of the window's state. """

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors.main_bg)
        self.app = app
        self.state = app.app_state

        main, _side = two_columns(self, app)
        self.build_extraction(main)

    def build_extraction(self, main):
        """ The card with the path of the extraction and the buttons that fill it in. """
        card = Card(main, self.app, "EXTRACTION")
        card.grid(row=0, column=0, sticky="ew")
        card.body.columnconfigure(0, weight=1)

        field = LabeledEntry(card.body, self.app,
                             Field("File or folder", self.state.run.source))
        field.grid(row=0, column=0, sticky="ew")
        self.entry = field.entry
        Tooltip((field.box, field.entry), self.app, self.images_text)

        buttons = tk.Frame(card.body, bg=card.background)
        buttons.grid(row=1, column=0, sticky="w", pady=(12, 0))
        created = {}
        for text, command in (("Folder…", self.choose_folder), ("Files…", self.choose_files),
                              ("Recent ▾", self.show_recent)):
            created[text] = OutlineButton(buttons, self.app, text=text, command=command,
                                          style="in_card")
            created[text].pack(side="left", padx=(0, 8))
        self.recent_button = created["Recent ▾"]

        Caption(card.body, self.app, leapp.source_hint, card.background).grid(
            row=2, column=0, sticky="ew", pady=(12, 0))

        self.recent_menu = tk.Menu(self, tearoff=0)

    def focus_input(self):
        """ Put the cursor in the source field: Ctrl+I """
        self.entry.focus_set()

    def images_text(self):
        """ What the tooltip says: the images picked together, nothing for one path. """
        paths = self.state.source_paths()
        if len(paths) < 2:
            return ""
        return f"{len(paths)} images, read together:\n" + "\n".join(paths)

    def choose_folder(self):
        """ Ask for a folder: an extraction already unpacked, an iTunes backup or an image folder. """
        folder = filedialog.askdirectory(parent=self.winfo_toplevel(), title="Select a folder")
        if folder:
            self.pick([folder])

    def choose_files(self):
        """ Ask for a file, or for several: the disk images of a RAID set. """
        picked = filedialog.askopenfilenames(
            parent=self.winfo_toplevel(), title="Select a file (or the disk images of a RAID set)",
            filetypes=FILE_TYPES)
        if picked:
            self.pick(list(self.tk.splitlist(picked)))

    def pick(self, paths):
        """ Take paths as the source and remember them in the history, as one set when there are several. """
        self.state.set_source(paths)
        if len(paths) > 1:
            history.record_input_set(paths)
        else:
            history.record_input_path(paths[0])

    def show_recent(self):
        """ Open the menu of the recent paths and sets of images under its button. """
        menu = self.recent_menu
        menu.delete(0, "end")
        if not history.is_history_enabled():
            menu.add_command(label="(History disabled - enable it in Settings)", state="disabled")
        else:
            paths = history.get_input_paths()
            if not paths:
                menu.add_command(label="(No recent paths)", state="disabled")
            for path in paths:
                menu.add_command(label=history.format_path_for_display(path),
                                 command=lambda path=path: self.state.set_source([path]))

            sets = []
            for input_set in history.get_input_sets():
                given = [path for path in input_set.get("paths", [])
                         if path not in input_set.get("found_automatically", [])]
                if len(given) > 1:
                    sets.append(given)
            if sets:
                menu.add_separator()
            for given in sets:
                menu.add_command(
                    label=selection_text([history.format_path_for_display(path) for path in given]),
                    command=lambda given=given: self.state.set_source(given))
        button = self.recent_button
        try:
            menu.tk_popup(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height())
        finally:
            menu.grab_release()
