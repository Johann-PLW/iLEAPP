"""
The Run screen: how far the run has gone, and its log.
"""

import os
import tkinter as tk
from tkinter import messagebox, ttk
from types import SimpleNamespace

from leapp_functions.app import artifact_list, new_run
from leapp_functions.app.run_worker import RunWorker
from leapp_functions.app.gui import themes
from leapp_functions.app.gui.custom_widgets import GAP, Card

POLL = 50  # milliseconds: the log still scrolls smoothly, and polling is not itself the load


def build_request(state):
    """ What a run needs. """
    run, artifacts = state.run, state.artifacts
    paths = state.source_paths()
    opened = run.unlock.result if run.unlock is not None else None
    raw = run.detected.kind == "raw"
    return SimpleNamespace(plugins=artifact_list.run_order(artifacts), loader=artifacts.loader,
                           detected=run.detected, paths=paths, single_file=run.single_file.get(),
                           input_path=opened.input_path if raw else paths[0],
                           image_keys=opened.keys if raw else None, found=opened if raw else None,
                           backup_keys=None if raw else opened,
                           case=state.case_values(),
                           profile=artifact_list.profile_for_report(artifacts),
                           hash_files=run.hash_files.get(),
                           output=os.path.abspath(run.output.get().strip()),
                           folder_name=run.folder_name.get().strip(),
                           secrets={name: variable.get().strip()
                                    for name, variable in run.secrets.items()},
                           out_params=None)


class RunControl:
    """ Starts the run and follows it, whatever the screen on show. """

    def __init__(self, app, crunch):
        self.app = app
        self.crunch = crunch
        self.watch_id = None

    def start(self):
        """ Start the run on its worker thread. """
        state = self.app.app_state
        if state.missing_for("run"):
            return
        state.run.worker = RunWorker(build_request(state), self.crunch)
        state.run_status = "running"
        self.app.go("run")
        self.watch()

    def watch(self):
        """ Show what the run has reported, until it ends. """
        worker = self.app.app_state.run.worker
        worker.poll()
        self.app.widgets["screen"].refresh()
        if worker.shown.outcome is None:
            self.watch_id = self.app.after(POLL, self.watch)
        else:
            self.watch_id = None
            self.over(worker.shown)

    def over(self, shown):
        """ The worker has ended. """
        state = self.app.app_state
        if shown.outcome == "refused":
            state.run_status = "idle"
            state.run.worker = None
            self.app.go("review")
            state.detect_source()
            messagebox.showerror("The run did not start", shown.detail, parent=self.app)
            return
        state.run_status = "finished"
        self.app.refresh_steps()
        if shown.outcome == "failed":
            message = "Processing failed. See the log for details."
            if shown.log_file:
                message += f"\nLog file located at {shown.log_file}"
            messagebox.showerror("Error", message, parent=self.app)

    def new_run(self):
        """ Start the program again, which keeps nothing of this run, and leave. """
        try:
            new_run.start()
        except OSError as error:
            messagebox.showerror("The new run did not start", str(error), parent=self.app)
            return
        self.app.destroy()

    def stop_watching(self):
        """ The window goes. """
        if self.watch_id is not None:
            self.app.after_cancel(self.watch_id)
            self.watch_id = None


class RunScreen(tk.Frame):
    """ The progress of the run and its log. """

    def __init__(self, parent, app):
        colors = app.colors
        super().__init__(parent, bg=colors.main_bg)
        self.worker = app.app_state.run.worker
        self.written = 0
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        card = Card(self, app, "PROGRESS")
        card.grid(row=0, column=0, sticky="ew")
        self.count = tk.Label(card.body, anchor="w", bg=card.background, fg=colors.text_primary,
                              font=themes.sans(12))
        self.count.pack(fill="x")
        self.progress_bar = ttk.Progressbar(card.body, style="Run.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(6, 0))

        card = Card(self, app, "LOG")
        card.grid(row=1, column=0, sticky="nsew", pady=(GAP, 0))
        card.body.rowconfigure(0, weight=1)
        card.body.columnconfigure(0, weight=1)
        self.log = tk.Text(card.body, height=1, wrap="char", state="disabled", relief="flat",
                           borderwidth=0, highlightthickness=0, padx=3, bg=card.background,
                           fg=colors.text_primary, selectbackground=colors.line,
                           selectforeground=colors.text_primary, font=themes.mono(12))
        self.log.grid(row=0, column=0, sticky="nsew")
        self.log.bind("<Map>", lambda _event: self.log.see("end"))
        scrollbar = ttk.Scrollbar(card.body, orient="vertical", command=self.log.yview,
                                  style="Card.Vertical.TScrollbar")
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.log.configure(yscrollcommand=scrollbar.set)

        self.refresh()

    def refresh(self):
        """ Show what the run has reported since the last call. """
        shown = self.worker.shown
        total = len(self.worker.request.plugins)
        self.progress_bar.configure(maximum=max(total, 1), value=shown.done)
        self.count.configure(text=f"{shown.done:,} of {total:,} artifacts done")
        if self.written == len(shown.log):
            return
        following = self.log.yview()[1] >= 1
        self.log.configure(state="normal")
        self.log.insert("end", "".join(shown.log[self.written:]))
        self.log.configure(state="disabled")
        self.written = len(shown.log)
        if following:
            self.log.see("end")
