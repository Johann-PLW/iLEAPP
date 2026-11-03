"""
A run of the parser on a thread of its own: the window stays usable and reads what it reports.
"""

import os
import queue
import threading
import traceback
from types import SimpleNamespace

from leapp_functions import leapp
from leapp_functions.app import history, input_type
from leapp_functions.app.output import resolve_output_folder_name, validate_output_folder_available
from scripts.context import Context
from scripts.ilapfuncs import GuiWindow, OutputParameters, is_platform_windows, logfunc
from scripts.lavafuncs import initialize_lava, lava_finalize_output, lava_json_name
from scripts.raw_image import input_text

SOURCE_CHANGED = "The extraction has changed since it was chosen: check it on the Source screen."


def long_path(path):
    """ Extractions can hold paths over 260 characters: Windows needs \\\\?\\ in front of them. """
    return "\\\\?\\" + path.replace("/", "\\") if path[1:2] == ":" else path


def short_path(path):
    """ A path as the examiner gave it, for showing it. """
    return path[4:] if path.startswith("\\\\?\\") else path


class RunWorker:
    """ One run. The worker thread only reports on a queue, which the window reads with poll(). """

    def __init__(self, request, crunch):
        """
        Args:
            request (SimpleNamespace): what the run needs, see run.build_request.
            crunch (function): calls the crunch_artifacts of this LEAPP with a request.
        """
        self.request = request
        self.crunch = crunch
        self.messages = GuiWindow.message_queue = queue.Queue()
        self.shown = SimpleNamespace(log=[], done=0, outcome=None, detail="", folder="",
                                     log_file="", stopping=False)
        threading.Thread(target=self.work, daemon=True).start()

    def stop(self):
        """ Ask the run to stop once the artifact in progress has ended. """
        GuiWindow.stop_requested = True
        self.shown.stopping = True

    def refusal(self):
        """ Why the run must not start. """
        request = self.request
        detected = input_type.detect(request.paths, single_file=request.single_file)
        if detected != request.detected:
            return SOURCE_CHANGED
        _valid, error = validate_output_folder_available(request.output, request.folder_name)
        return error or ""

    def work(self):
        """ The worker thread. Everything that may wait on a disk is here, not in the window.
        A sqlite3 connection only works on the thread that opened it, so LAVA is opened here. """
        outcome = None
        try:
            self.prepare()
            problem = self.refusal()
            outcome = ("refused", problem) if problem else ("done", self.parse())
        finally:
            self.messages.put(outcome or ("failed", traceback.format_exc()))

    def prepare(self):
        """ The paths of the run, and the name of its report folder. """
        request = self.request
        request.folder_name = resolve_output_folder_name(request.folder_name)
        if is_platform_windows():
            request.output = long_path(request.output)
            if request.detected.kind == "fs":
                request.input_path = long_path(request.input_path)

    def parse(self):
        """ The run itself.
        Returns:
            bool: what crunch_artifacts says, False when it could not read the source.
        """
        request = self.request
        out_params = request.out_params = OutputParameters(request.output, request.folder_name)
        Context.set_output_params(out_params)
        self.shown.folder = short_path(out_params.output_folder_base)
        self.shown.log_file = short_path(out_params.screen_output_file_path)

        if isinstance(request.input_path, list):
            history.record_input_set(request.input_path, getattr(request.found, "found", request.found))
        else:
            history.record_input_path(request.input_path)
        history.record_output_path(request.output)

        initialize_lava(input_text(request.input_path, request.found),
                        out_params.output_folder_base, request.detected.kind, request.profile)
        successful = self.crunch(request)
        lava_finalize_output(out_params.output_folder_base,
                             "Stopped" if GuiWindow.stopped else "Complete")
        if successful and not GuiWindow.stopped:
            history.record_recent_run(leapp.name.lower(), leapp.version,
                                      os.path.join(out_params.output_folder_base, lava_json_name))
        return successful

    def poll(self):
        """ Take in what the worker has reported, on the Tk thread. Never waits. """
        shown = self.shown
        while shown.outcome is None:
            try:
                kind, payload = self.messages.get_nowait()
            except queue.Empty:
                return
            if kind == "log":
                shown.log.append(payload)
            elif kind == "progress":
                shown.done = payload
            else:
                self.finish(kind, payload)

    def finish(self, kind, payload):
        """ The worker has ended: "refused", "failed", or "done" with what the run returned. """
        shown = self.shown
        if kind == "done":
            shown.outcome = ("stopped" if GuiWindow.stopped else "done") if payload else "failed"
        else:
            shown.outcome, shown.detail = kind, payload
        GuiWindow.end_worker_run()
        if kind == "failed":
            logfunc("Processing failed with an unhandled error:")
            logfunc(payload)
            shown.log.append(f"Processing failed with an unhandled error:\n{payload}\n")
