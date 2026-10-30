"""
What the window shows, kept apart from the widgets that show it.
The widgets are destroyed and built again whenever the palette changes, so anything that
has to outlive them, such as the case data typed so far, lives here.
"""

import base64
import tkinter as tk
from types import SimpleNamespace

from leapp_functions.app import input_type
from scripts.filetype import guess_mime
from scripts.raw_image import selected_paths, selection_text

ORDER = ("case", "source", "artifacts", "review", "run", "results")
STAGE_OF = {"review": "run"}

CASE_KEYS = {"Case Number": "number", "Agency": "agency", "Agency Logo Path": "logo_path",
             "Agency Logo mimetype": "logo_mimetype", "Agency Logo base64": "logo_base64",
             "Examiner": "examiner", "Notes": "notes"}


class AppState:
    """ Tk variables that widgets can show and edit directly. """

    def __init__(self, on_change):
        self.on_change = on_change
        self.step = "case"
        self.left = set()  # the steps the user has moved on from
        self.case = SimpleNamespace(number=tk.StringVar(),
                                    agency=tk.StringVar(), examiner=tk.StringVar(),
                                    notes=tk.StringVar(), logo_path=tk.StringVar(),
                                    logo_mimetype=tk.StringVar(), logo_base64=tk.StringVar())

        self.run = SimpleNamespace(source=tk.StringVar(), output=tk.StringVar(), selection=[],
                                   detected=None)
        self.selected_artifacts = set()

        self.run_status = "idle"  # "idle" until a run starts, then "running", then "finished"

    def case_values(self):
        """ Return case data using the keys expected in a case data file."""
        return {key: getattr(self.case, name).get() for key, name in CASE_KEYS.items()}

    def load_case_values(self, values):
        """ Fill case data fields from CASE_KEYS dictionary. """
        for key, name in CASE_KEYS.items():
            getattr(self.case, name).set(str(values.get(key, "")))

    def case_is_empty(self):
        """ Whether every field of the case data is empty. """
        return not any(self.case_values().values())

    def clear_case(self):
        """ Empty every field of the case data. """
        self.load_case_values({})

    def set_logo(self, path):
        """
        Picture of the agency logo: its path, its MIME type and its content in base64.
        Raises:
            ValueError: the file cannot be read or is not a picture. The case data is left as it was.
        """
        try:
            mimetype = guess_mime(path)
            with open(path, "rb") as logo_file:
                encoded = base64.b64encode(logo_file.read()).decode("ascii")
        except OSError as error:
            raise ValueError(f"Unable to read {path}: {error.strerror}") from error
        if not mimetype or not mimetype.startswith("image/"):
            raise ValueError("The selected file is not a valid picture file.")
        self.case.logo_path.set(path)
        self.case.logo_mimetype.set(mimetype)
        self.case.logo_base64.set(encoded)

    def set_source(self, paths):
        """ Show the files picked in the source field: one path, or the first and how many more. """
        paths = list(paths)
        self.run.selection = paths if len(paths) > 1 else []
        self.run.source.set(selection_text(paths))

    def source_paths(self):
        """ The input the source field stands for. """
        return [path for path in selected_paths(self.run.source.get().strip(), self.run.selection)
                if path]

    def detect_source(self):
        """ Look at the source. """
        detected = input_type.detect(self.source_paths())
        if detected != self.run.detected:
            self.run.detected = detected
            self.on_change()

    def missing_for_source(self):
        """ Why the source cannot be read before running processes. """
        detected = self.run.detected
        if detected is None:
            return "Select an extraction first: nothing can be parsed without one."
        return "" if detected.kind else detected.problem

    def stage(self):
        """The step of the five under the header that the screen on show belongs to."""
        return STAGE_OF.get(self.step, self.step)

    def neighbour(self, offset):
        """The screen before or after the one on show, None at either end."""
        index = ORDER.index(self.step) + offset
        return ORDER[index] if 0 <= index < len(ORDER) else None

    def missing_for_run(self):
        """What a run still needs: an extraction, an output folder and at least one artifact."""
        missing = self.missing_for_source()
        if missing:
            return missing
        if not self.run.output.get().strip():
            return "Choose an output folder."
        if not self.selected_artifacts:
            return "No artifact selected."
        return ""

    def ready_to_run(self):
        """ Whether a run has everything it needs: an extraction, an output folder and at least
        one artifact. """
        return not self.missing_for_run()

    def can_go(self, step):
        """
        Whether the user may move to a step, given by its key.
        Case, Source and Artifacts are always open, Artifacts too without an extraction so that the
        artifacts can be looked at and a profile loaded first. Run needs everything a run needs,
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
        """ The steps done, shown with a tick.
        The case data is optional: the step is done once the user has moved on from it.
        The source is done once it can be read.
        """
        done = set()
        if "case" in self.left or not self.case_is_empty():
            done.add("case")
        if not self.missing_for_source():
            done.add("source")
        return done
