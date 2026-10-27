"""
What the window shows, kept apart from the widgets that show it.
The widgets are destroyed and built again whenever the palette changes, so anything that
has to outlive them, such as the case data typed so far, lives here.
"""

import tkinter as tk
from types import SimpleNamespace

ORDER = ("case", "source", "modules", "review", "run", "results")
STAGE_OF = {"review": "run"}


class AppState:
    """ Tk variables that widgets can show and edit directly. """

    def __init__(self, on_change):
        self.on_change = on_change
        self.step = "case"

        # Case data, typed on the Case screen
        self.case = SimpleNamespace(number=tk.StringVar(), name=tk.StringVar(),
                                    agency=tk.StringVar(), examiner=tk.StringVar(),
                                    notes=tk.StringVar())

        self.source = tk.StringVar()
        self.output = tk.StringVar()
        self.selected_modules = set()

        # "idle" until a run starts, then "running", then "finished"
        self.run_status = "idle"

    def stage(self):
        """The step of the five under the header that the screen on show belongs to."""
        return STAGE_OF.get(self.step, self.step)

    def neighbour(self, offset):
        """The screen before or after the one on show, None at either end."""
        index = ORDER.index(self.step) + offset
        return ORDER[index] if 0 <= index < len(ORDER) else None

    def missing_for_run(self):
        """What a run still needs: an extraction, an output folder and at least one module."""
        if not self.source.get().strip():
            return "Select an extraction first: nothing can be parsed without one."
        if not self.output.get().strip():
            return "Choose an output folder."
        if not self.selected_modules:
            return "No module selected."
        return ""

    def ready_to_run(self):
        """ Whether a run has everything it needs: an extraction, an output folder and at least
        one module. """
        return not self.missing_for_run()

    def can_go(self, step):
        """
        Whether the user may move to a step, given by its key.
        Case, Source and Modules are always open, Modules too without an extraction so that the
        modules can be looked at and a profile loaded first. Run needs everything a run needs,
        and Results a run that has taken place. While a run is on, nothing else can be reached.
        """
        if self.run_status == "running":
            return step == "run"
        if step in ("review", "run"):
            return self.ready_to_run()
        if step == "results":
            return self.run_status == "finished"
        return True

    def completed(self):
        """ The steps done, shown with a tick: a set of the keys used by step. """
        done = set()
        case_values = (self.case.number, self.case.name, self.case.examiner)
        if any(value.get().strip() for value in case_values):
            done.add("case")
        return done
