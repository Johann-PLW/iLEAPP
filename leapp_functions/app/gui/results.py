"""
The Results screen.
"""

import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from leapp_functions import leapp
from leapp_functions.app.gui import themes
from leapp_functions.app.gui.custom_widgets import (Card, OutlineButton, mark_line, two_columns,
                                                    wrap_to_width)
from leapp_functions.lava_launcher import LAVA_WEBSITE, open_lava_project, open_output_folder
from scripts import ilapfuncs
from scripts.lavafuncs import lava_json_name

KEY_WIDTH = 104
ROW_GAP = 8
BUTTON_GAP = 8
REPORT_FILE = "index.html"
TSV_FOLDER = "_TSV Exports"
ERRORS_SHOWN = 6


def lava_only_count():
    """ How many artifacts of the run have no page in the HTML report. """
    groups = getattr(ilapfuncs, "lava_only_artifacts", {})
    return sum(len(artifacts) for artifacts in groups.values())


def notices(worker):
    """ What the examiner should know about what the run has written. """
    shown = worker.shown
    if shown.outcome == "failed":
        return [("problem", "The run failed: the report may be missing or incomplete. "
                            "The log on the Run screen says why.")]
    lines = []
    if shown.summary.errors:
        lines.append(("problem", f"Artifacts with errors: {len(shown.summary.errors):,}. "
                                 "The log on the Run screen says why."))
    if shown.outcome == "stopped":
        left = shown.total - shown.done
        lines.append(("attention", f"Incomplete report, artifacts not run: {left:,}. An artifact "
                                   "missing from this report may still have data in the extraction."))
    count = lava_only_count()
    if count:
        lines.append(("attention", f"Artifacts with too much data to be viewed in a Web browser: "
                                   f"{count:,}. See the 'LAVA only artifacts' tab of the report "
                                   "for how to view them."))
    return lines or [("ok", "Nothing needs your attention.")]


def result_rows(worker):
    """ The lines of the summary: (key, value). """
    shown = worker.shown
    rows = [("Artifacts", f"{shown.done:,} of {shown.total:,} run")]
    summary = shown.summary
    if summary is not None and shown.outcome != "failed":
        files = f"{summary.with_files:,} artifacts · {summary.without_files:,} without files"
        if summary.errors:
            files += f" · {len(summary.errors):,} with errors"
        rows.append(("Files found", files))
        rows.append(("Run time", summary.run_time))
    if shown.folder:
        rows.append(("Report folder", shown.folder))
    if shown.outcome == "failed" and shown.log_file:
        rows.append(("Log file", shown.log_file))
    return rows


class ErrorList(tk.Frame):
    """ The artifacts with errors. """

    def __init__(self, parent, app, background, names):
        colors = app.colors
        super().__init__(parent, bg=background)
        self.columnconfigure(0, weight=1)
        self.text = tk.Text(self, width=1, height=1, wrap="word", bd=0, highlightthickness=0,
                            padx=3, pady=0, bg=background, fg=colors.text_primary,
                            font=themes.sans(11), selectbackground=colors.line,
                            selectforeground=colors.text_primary)
        self.text.tag_configure("name", lmargin2=12)
        self.text.insert("1.0", "\n".join(names), "name")
        self.text.configure(state="disabled")
        self.text.grid(row=0, column=0, sticky="ew")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview,
                                       style="Card.Vertical.TScrollbar")
        self.scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.text.configure(yscrollcommand=self.scrollbar.set)
        self.text.bind("<Configure>", lambda _event: self.fit())

    def fit(self):
        """ The width is known: a long name may take two lines, so the names cannot be counted. """
        lines = self.text.tk.getint(
            self.text.tk.call(self.text, "count", "-update", "-displaylines", "1.0", "end"))
        self.text.configure(height=min(lines, ERRORS_SHOWN))
        if lines > ERRORS_SHOWN:
            self.scrollbar.grid()
        else:
            self.scrollbar.grid_remove()


class ResultsScreen(tk.Frame):
    """ The end of the run. """

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors.main_bg)
        self.app = app
        self.worker = app.app_state.run.worker
        main, side = two_columns(self, app)
        self.build_result(main)
        card = Card(side, app, "WHAT TO KNOW", accent=True)
        card.pack(fill="x")
        card.body.columnconfigure(1, weight=1)
        row = 0
        for status, text in notices(self.worker):
            mark_line(card, app, row, status, text)
            row += 1
            if status == "problem" and self.worker.shown.outcome != "failed":
                errors = ErrorList(card.body, app, card.background, self.worker.shown.summary.errors)
                errors.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(4, 8))
                row += 1

    def build_result(self, main):
        """ The card with what the run has written, and the buttons that open it. """
        card = Card(main, self.app, "RESULT")
        card.grid(row=0, column=0, sticky="ew")
        self.build_rows(card)

        written = self.worker.shown.outcome != "failed"
        launcher = self.worker.shown.lava_launcher
        folder = self.worker.shown.folder
        buttons = tk.Frame(card.body, bg=card.background)
        buttons.pack(anchor="w", pady=(14, 0))
        buttons.columnconfigure((0, 2), uniform="button")
        buttons.columnconfigure(1, minsize=BUTTON_GAP)
        for index, (text, command, enabled) in enumerate((
                ("Open HTML report", self.open_report, written),
                ("Open in LAVA", self.open_lava, written) if launcher
                else ("Explore LAVA", self.explore_lava, True),
                ("Open TSV Folder", self.open_tsv_folder,
                 bool(folder) and os.path.isdir(os.path.join(folder, TSV_FOLDER))),
                ("Open output folder", self.open_folder, bool(folder)))):
            button = OutlineButton(buttons, self.app, style="in_card", text=text, command=command)
            row, column = divmod(index, 2)
            button.grid(row=row, column=column * 2, sticky="ew", pady=(row * BUTTON_GAP, 0))
            button.set_enabled(enabled)

    def build_rows(self, card):
        """ The lines of the summary, in the card. """
        colors = self.app.colors
        rows = tk.Frame(card.body, bg=card.background)
        rows.pack(fill="x")
        rows.columnconfigure(0, minsize=KEY_WIDTH)
        rows.columnconfigure(1, weight=1)
        for row, (key, value) in enumerate(result_rows(self.worker)):
            tk.Label(rows, text=key, anchor="w", bg=card.background, fg=colors.text_secondary,
                     font=themes.sans(12)).grid(row=row, column=0, sticky="nw", pady=(ROW_GAP, 0))
            shown = tk.Label(rows, text=value, anchor="w", justify="left", width=1,
                             bg=card.background, fg=colors.text_primary, font=themes.sans(12))
            shown.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=(ROW_GAP, 0))
            shown.bind("<Configure>", wrap_to_width)

    def open_in_browser(self, url):
        """ Open a page in the default browser. """
        if not webbrowser.open_new_tab(url):
            messagebox.showerror("Unable to open a browser", f"{leapp.name} could not open:\n{url}",
                                 parent=self.app)

    def open_report(self):
        """ The HTML report. as_uri() also handles a network path, spaces and a # in the path. """
        self.open_in_browser(Path(self.worker.shown.folder, REPORT_FILE).as_uri())

    def explore_lava(self):
        """ The LAVA website. """
        self.open_in_browser(LAVA_WEBSITE)

    def open_lava(self):
        """ The project in LAVA. """
        shown = self.worker.shown
        try:
            open_lava_project(os.path.join(shown.folder, lava_json_name), shown.lava_launcher,
                              ilapfuncs.logfunc)
        except (OSError, ValueError) as error:
            messagebox.showerror("Unable to open LAVA",
                                 f"{leapp.name} could not open the project in LAVA:\n{error}",
                                 parent=self.app)

    def open_in_file_manager(self, folder, name):
        """ Open a folder in the file manager. """
        try:
            open_output_folder(folder)
        except OSError as error:
            messagebox.showerror(f"Unable to open {name}",
                                 f"{leapp.name} could not open the {name}:\n{error}",
                                 parent=self.app)

    def open_folder(self):
        """ The report folder. """
        self.open_in_file_manager(self.worker.shown.folder, "output folder")

    def open_tsv_folder(self):
        """ The folder of the TSV exports, in the report folder. """
        self.open_in_file_manager(os.path.join(self.worker.shown.folder, TSV_FOLDER), "TSV folder")
