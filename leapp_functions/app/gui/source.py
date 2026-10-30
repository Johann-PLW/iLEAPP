"""
The Source screen: the extraction to parse, where the keychain and the report go.
"""

import tkinter as tk
from tkinter import filedialog

from leapp_functions import leapp
from leapp_functions.app import history, input_type
from leapp_functions.app.gui import themes
from leapp_functions.app.gui.custom_widgets import (Caption, Card, Field, LabeledEntry,
                                                    OutlineButton, Tooltip, two_columns)
from scripts.raw_image import (RAW_IMAGE_FILE_PATTERNS, RAW_IMAGE_LABEL, confirm_found_members,
                               selection_text)

FILE_TYPES = (("All supported files", "*.tar *.zip *.gz *.xz " + RAW_IMAGE_FILE_PATTERNS),
              ("tar file", "*.tar"), ("zip file", "*.zip"), ("gz file", "*.gz"),
              ("tar.xz file", "*.xz"), (RAW_IMAGE_LABEL, RAW_IMAGE_FILE_PATTERNS))
DETECT_DELAY = 300
POLL_DELAY = 100


class SourceScreen(tk.Frame):
    """ The fields of the Source screen, which edit the variables of the window's state. """

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors.main_bg)
        self.app = app
        self.state = app.app_state

        main, side = two_columns(self, app)
        self.build_extraction(main)
        DetectedCard(side, app).pack(fill="x")

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


class DetectedCard(tk.Frame):
    """ The card on the right of the Source screen: what the source is, as the run will read it. """

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors.main_bg)
        self.app = app
        card = Card(self, app, "DETECTED", accent=True)
        card.pack(fill="x")
        self.kind = Caption(card.body, app, "", card.background)
        self.kind.configure(fg=app.colors.text_primary, font=themes.sans(13, "bold"))
        self.kind.pack(fill="x")
        self.detail = Caption(card.body, app, "", card.background)
        self.unlock_panel = UnlockPanel(card.body, app, card.background)
        self.unlock_panel.pack(fill="x")

        self.pending = None
        variable = app.app_state.run.source
        trace = variable.trace_add("write", lambda *_args: self.schedule())
        self.bind("<Destroy>", lambda _event: self.stop(variable, trace))
        self.refresh()

    def schedule(self):
        """ Look at the source a moment after the last change of the field. """
        if self.pending is not None:
            self.after_cancel(self.pending)
        self.pending = self.after(DETECT_DELAY, self.refresh)

    def stop(self, variable, trace):
        """ The card is destroyed: the field is no longer watched for it. """
        variable.trace_remove("write", trace)
        if self.pending is not None:
            self.after_cancel(self.pending)

    def refresh(self):
        """ Show what the source is. """
        self.pending = None
        colors, state = self.app.colors, self.app.app_state
        state.detect_source()
        detected = state.run.detected
        if detected is None:
            detected = input_type.Detected("", "Nothing selected",
                                           note="The type of the extraction shows here once it is chosen.")
        self.kind.configure(text=detected.label)
        detail = detected.problem or detected.note
        self.detail.configure(text=detail, fg=colors.text_leapp_color if detected.problem
                              else colors.text_secondary)
        if detail:
            self.detail.pack(fill="x", pady=(6, 0), before=self.unlock_panel)
        else:
            self.detail.pack_forget()
        self.unlock_panel.restart()


class UnlockPanel(tk.Frame):
    """ Under what the source is: the questions asked to open it, one at a time. """

    def __init__(self, parent, app, background):
        super().__init__(parent, bg=background)
        self.app = app
        self.background = background
        self.secret = tk.StringVar()
        self.shown = None
        self.polling = None
        self.bind("<Destroy>", lambda _event: self.stop())

    def stop(self):
        """ No more looking for questions. """
        if self.polling is not None:
            self.after_cancel(self.polling)
            self.polling = None

    def restart(self):
        """ Look for the questions of the source's sequence, a new one or the one already running. """
        self.stop()
        self.poll()

    def poll(self):
        """ Show what the sequence asks, and look again a moment later while it runs.
        The window takes the questions in (MainWindow.watch_unlock): this only shows them. """
        self.polling = None
        unlock = self.app.app_state.run.unlock
        if unlock is not None:
            if not unlock.shown.done:
                self.polling = self.after(POLL_DELAY, self.poll)
        # Built again only when what it shows has changed, so as not to clear a field being typed in
        shown = (unlock, unlock.shown.waiting, unlock.shown.message,
                 unlock.shown.done) if unlock else None
        if shown != self.shown:
            self.shown = shown
            self.build(unlock)

    def build(self, unlock):
        """ The message, then the question waiting for an answer, or what the sequence is doing. """
        for child in self.winfo_children():
            child.destroy()
        if unlock is None:
            return
        tk.Frame(self, bg=self.background, height=12).pack(fill="x")
        colors = self.app.colors
        message = unlock.shown.message
        if message is not None:
            self.text(message.text, colors.text_leapp_color if message.kind == "error"
                      else colors.text_secondary)
        question = unlock.shown.waiting
        if question is None:
            self.build_status(unlock)
        elif question.kind == "secret":
            self.build_secret(unlock, question)
        elif question.kind == "file":
            self.text(question.title, colors.text_primary)
            self.buttons(("Choose…", lambda: self.choose_file(unlock, question)),
                         ("Cancel", lambda: unlock.answer(None)))
        else:
            self.text("Other members of the RAID set were found beside this image.",
                      colors.text_primary)
            self.buttons(("Review…", lambda: unlock.answer(
                confirm_found_members(self.winfo_toplevel(), question.extra))),
                         ("Cancel", lambda: unlock.answer(None)))

    def build_status(self, unlock):
        """ No question: the sequence is still reading the source, or it has ended. """
        colors = self.app.colors
        if not unlock.shown.done:
            self.text("Opening the source…", colors.text_secondary)
        elif unlock.result is not None and unlock.shown.locked:
            self.text("Opened. Locked volumes are not read.", colors.text_secondary)
        elif unlock.result is not None:
            self.text("Opened: ready to be read.", colors.text_secondary)
        else:
            self.text("Not opened.", colors.text_leapp_color)
            self.buttons(("Try again", self.try_again))

    def build_secret(self, unlock, question):
        """ A password to type, hidden, with the question above it. """
        self.text(question.text, self.app.colors.text_primary)
        field = LabeledEntry(self, self.app, Field(question.title, self.secret),
                             background=self.background)
        field.entry.configure(show="•")
        field.entry.bind("<Return>", lambda _event: self.send_secret(unlock))
        field.pack(fill="x", pady=(8, 0))
        self.buttons(("Unlock", lambda: self.send_secret(unlock)),
                     ("Cancel", lambda: unlock.answer(None)))

    def text(self, text, color):
        """ A line of text, on as many lines as it needs. """
        caption = Caption(self, self.app, text, self.background)
        caption.configure(fg=color)
        caption.pack(fill="x", pady=(0, 6))

    def buttons(self, *buttons):
        """ A row of buttons, each given as (text, command). Any answer shows what comes next at once. """
        row = tk.Frame(self, bg=self.background)
        row.pack(fill="x", pady=(8, 0))
        for text, command in buttons:
            OutlineButton(row, self.app, text=text, command=lambda command=command: self.then(command),
                          style="in_card").pack(side="left", padx=(0, 8))

    def then(self, command):
        """ Run a button's command, then show at once what it changed. """
        command()
        self.app.app_state.poll_unlock()
        self.restart()

    def send_secret(self, unlock):
        """ Give the password typed to the sequence, and forget it here. """
        secret = self.secret.get()
        self.secret.set("")
        unlock.answer(secret)
        self.app.app_state.poll_unlock()
        self.restart()

    def choose_file(self, unlock, question):
        """ Answer with the file chosen in a file dialog, None when it is cancelled. """
        path = filedialog.askopenfilename(parent=self.winfo_toplevel(), title=question.title,
                                          filetypes=question.extra)
        unlock.answer(path or None)

    def try_again(self):
        """ Run the sequence of the same source again. """
        self.app.app_state.start_unlock()
