"""
What the window shows, kept apart from the widgets that show it.
The widgets are destroyed and built again whenever the palette changes, so anything that
has to outlive them, such as the case data typed so far, lives here.
"""

import tkinter as tk
from types import SimpleNamespace


class AppState:
    """ Tk variables that widgets can show and edit directly. """

    def __init__(self, on_change):
        self.on_change = on_change
        self.step = "case"

        # Case data, typed on the Case screen
        self.case = SimpleNamespace(number=tk.StringVar(), name=tk.StringVar(),
                                    examiner=tk.StringVar())

        self.source = tk.StringVar()
        self.output = tk.StringVar()
        self.selected_modules = set()

        # "idle" until a run starts, then "running", then "finished"
        self.run_status = "idle"

    def ready_to_run(self):
        """ Whether a run has everything it needs: an extraction, an output folder and at least
        one module. """
        return bool(self.source.get().strip() and self.output.get().strip()
                    and self.selected_modules)

    def can_go(self, step):
        """
        Whether the user may move to a step, given by its key.
        Case, Source and Modules are always open, Modules too without an extraction so that the
        modules can be looked at and a profile loaded first. Run needs everything a run needs,
        and Results a run that has taken place. While a run is on, nothing else can be reached.
        """
        if self.run_status == "running":
            return step == "run"
        if step == "run":
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
