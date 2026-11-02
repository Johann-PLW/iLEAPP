"""
The Review screen: what the run will read and write, before it starts.
"""

import tkinter as tk

from leapp_functions.app import artifact_list
from leapp_functions.app.gui import themes
from leapp_functions.app.gui.custom_widgets import Card, two_columns, wrap_to_width
from leapp_functions.app.output import default_output_folder_name

KEY_WIDTH = 104
ROW_GAP = 8
NONE = "None"


def artifacts_text(artifacts):
    """ How many artifacts will run, and how many of them are slow or large. """
    text = f"{len(artifacts.selected)} of {len(artifacts.listed)} selected"
    slow = sum(not artifact.default and artifact.name in artifacts.selected
               for artifact in artifacts.listed)
    return f"{text} · {slow} slow or large" if slow else text


def summary_rows(state):
    """ The lines of the summary: (key, value). """
    run, case = state.run, state.case
    filled = [variable.get() for variable in (case.number, case.agency, case.examiner) if variable.get()]
    return (("Case", " · ".join(filled) or "No case data"),
            ("Extraction", "\n".join(state.source_paths())),
            ("Read as", run.detected.label),
            *((name.capitalize(), variable.get() or NONE) for name, variable in run.secrets.items()),
            ("Artifacts", artifacts_text(state.artifacts)),
            ("Profile", artifact_list.profile_for_report(state.artifacts) or NONE),
            ("Output folder", run.output.get().strip()),
            ("Report folder", run.folder_name.get().strip()
             or f"Automatic: {default_output_folder_name()}"))


class ReviewScreen(tk.Frame):
    """ The summary of the run. Nothing can change while it is on show, so it is built once. """

    def __init__(self, parent, app):
        colors = app.colors
        super().__init__(parent, bg=colors.main_bg)
        main, _side = two_columns(self, app)

        card = Card(main, app, "RUN SUMMARY")
        card.grid(row=0, column=0, sticky="ew")
        card.body.columnconfigure(0, minsize=KEY_WIDTH)
        card.body.columnconfigure(1, weight=1)
        for row, (key, value) in enumerate(summary_rows(app.app_state)):
            tk.Label(card.body, text=key, anchor="w", bg=card.background, fg=colors.text_secondary,
                     font=themes.sans(12)).grid(row=row, column=0, sticky="nw", pady=(ROW_GAP, 0))
            shown = tk.Label(card.body, text=value, anchor="w", justify="left", width=1,
                             bg=card.background, fg=colors.text_primary, font=themes.sans(12))
            shown.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=(ROW_GAP, 0))
            shown.bind("<Configure>", wrap_to_width)
