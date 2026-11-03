"""
The new LEAPPs GUI --> Work in progress.
"""

import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import ileapp
from leapp_functions import leapp
from leapp_functions.app import artifact_list
from leapp_functions.app.gui import images, themes, window_area
from leapp_functions.app.gui.app_state import AppState
from leapp_functions.app.gui.header import Header
from leapp_functions.app.gui.steps import STAGES, Steps
from leapp_functions.app.gui.artifacts import ArtifactsScreen
from leapp_functions.app.gui.case import CaseScreen
from leapp_functions.app.gui.custom_widgets import ScrollArea
from leapp_functions.app.gui.review import ReviewScreen
from leapp_functions.app.gui.run import RunControl, RunScreen
from leapp_functions.app.gui.source import SourceScreen
from leapp_functions.app.gui.status_bar import StatusBar
from scripts.context import Context
from scripts.version_info import check_runtime_dependencies

MIN_SIZE = (900, 700)
UNLOCK_POLL = 100

TITLES = {key: title for key, title, _icon in STAGES} | {"review": "Review"}


class PlaceholderScreen(tk.Frame):
    """ An empty screen with its title, and a line that says it is not built yet. """

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors.main_bg)
        texts = tk.Frame(self, bg=app.colors.main_bg)
        texts.place(relx=0.5, rely=0.4, anchor="center")
        tk.Label(texts, text=TITLES[app.app_state.step], bg=app.colors.main_bg,
                 fg=app.colors.text_primary, font=themes.sans(28, "bold")).pack()
        tk.Label(texts, text="This screen does not exist yet: work in progress", bg=app.colors.main_bg,
                 fg=app.colors.text_secondary, font=themes.sans(14)).pack(pady=(6, 0))


SCREENS = {"case": CaseScreen, "source": SourceScreen, "artifacts": ArtifactsScreen,
           "review": ReviewScreen, "run": RunScreen}


def crunch(request):
    """ The parser. """
    Context.set_keychain_path(request.secrets.get("keychain") or None)
    return ileapp.crunch_artifacts(request.plugins, request.detected.kind, request.input_path,
                                   request.out_params, True, request.loader, request.case, "UTC",
                                   request.profile, None, request.backup_keys,
                                   image_password=request.image_keys, found_members=request.found,
                                   hash_files=request.hash_files)


class MainWindow(tk.Tk):
    """ Main application window for the LEAPP GUI. """

    def __init__(self):
        """ Initialize the window, application state, and widgets. """
        super().__init__()
        self.title(f"{leapp.name} version {leapp.version}")
        self.icon = images.load("icon.png")
        self.iconphoto(True, self.icon)
        self.screen_area = window_area.measure(self)
        self.minsize(MIN_SIZE[0], min(MIN_SIZE[1], self.screen_area[3]))

        self.app_state = AppState(self.refresh_steps)
        self.app_state.artifacts = artifact_list.load_artifacts()
        self.appearance = themes.Appearance(leapp.theme)
        ttk.Style(self).theme_use("clam")

        # Settings
        if sys.platform == "darwin":
            # On macOS: Settings item in the application menu and ⌘,
            self.createcommand("::tk::mac::ShowPreferences", self.open_settings)
            self.createcommand("::tk::mac::Quit", self.close)
        else:
            # Other platforms: Ctrl,
            self.bind_all("<Control-comma>", lambda _event: self.open_settings())

        self.bind("<Control-i>", lambda _event: self.focus_field("focus_input"))
        self.bind("<Control-o>", lambda _event: self.focus_field("focus_output"))
        self.bind("<Control-f>", lambda _event: self.focus_field("focus_search"))
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind(sequence, self.on_wheel)
        self.bind("<FocusIn>", self.on_focus)
        try:
            self.bind("<TouchpadScroll>", self.on_touchpad)
        except tk.TclError:
            pass

        self.protocol("WM_DELETE_WINDOW", self.close)

        self.widgets = {}
        self.unlock_watch = None
        self.run_control = RunControl(self, crunch)

        self.build()
        self.fix_size()
        self.watch_unlock()
        if sys.platform == "darwin":
            # the window has to be on screen first
            self.after(300, self.redraw)

    def on_wheel(self, event):
        """ The mouse wheel, anywhere in the window. """
        self.widgets["scroll"].wheel(event)

    def on_touchpad(self, event):
        """ The touchpad, anywhere in the window. """
        self.widgets["scroll"].touchpad(event)

    def on_focus(self, event):
        """ A widget has got the focus. """
        self.widgets["scroll"].reveal(event)

    def fix_size(self):
        """ Give the window the size its first screen asks for """
        self.update_idletasks()
        width = max(self.winfo_reqwidth(), MIN_SIZE[0])
        height = max(self.winfo_reqheight(), MIN_SIZE[1])
        window_area.place(self, self.screen_area, min(width, self.screen_area[2]),
                          min(height, self.screen_area[3]))

    def redraw(self):
        """ On macOS, a window opened from a terminal stays empty until it is clicked:
        resizing it by one pixel and back makes it draw. Then it is brought to the front. """
        width, height = self.winfo_width(), self.winfo_height()
        self.geometry(f"{width + 1}x{height}")
        self.update_idletasks()
        self.geometry(f"{width}x{height}")

        self.activate_application()

    def activate_application(self):
        """ Make the program the active application. """
        bundle = Path(sys.base_prefix) / "Resources" / "Python.app"
        if getattr(sys, "frozen", False) or not bundle.is_dir():
            return
        try:
            subprocess.run(["open", str(bundle)], check=False, timeout=5)
        except (OSError, subprocess.SubprocessError):
            pass

    @property
    def colors(self):
        """ The palette in use """
        return self.appearance.colors

    def build(self):
        """ Build or replace every widget using the current palette. """
        for name in ("header", "body"):
            if name in self.widgets:
                self.widgets[name].destroy()
        self.configure(bg=self.colors.main_bg)
        themes.apply_styles(ttk.Style(self), self.colors)
        if sys.platform == "darwin":
            appearance = "darkaqua" if self.appearance.is_dark else "aqua"
            try:
                self.tk.call("::tk::unsupported::MacWindowStyle", "appearance", self, appearance)
            except tk.TclError:
                pass  # Tk before 8.6.10 has no such setting

        self.widgets["header"] = Header(self, self)
        self.widgets["header"].pack(fill="x")

        body = self.widgets["body"] = tk.Frame(self, bg=self.colors.main_bg)
        body.pack(fill="both", expand=True, padx=16, pady=(16, 8))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        self.widgets["steps"] = Steps(body, self)
        self.widgets["steps"].grid(row=0, column=0, sticky="ew", pady=(0, 24))

        self.widgets["scroll"] = ScrollArea(body, self, self.fit_screen)
        self.widgets["scroll"].grid(row=1, column=0, sticky="nsew")

        self.show_screen()

        self.widgets["status_bar"] = StatusBar(body, self)
        self.widgets["status_bar"].grid(row=2, column=0, sticky="ew", pady=(16, 8))

    def show_screen(self):
        """ Build the screen of the step. What was typed is in the state, so it survives the screen being rebuilt. """
        old = self.widgets.pop("screen", None)
        if old is not None:
            old.destroy()
        step = self.app_state.step
        screen = SCREENS.get(step, PlaceholderScreen)(self.widgets["scroll"].content, self)
        self.widgets["screen"] = screen
        self.widgets["scroll"].show(screen)
        self.fit_screen()

    def fit_screen(self):
        """ Make the window bigger when the screen on show needs more room than it has, within the
        display: what still does not fit scrolls. It never gets smaller: a size the user gave it
        is kept when it is enough. It moves if it would leave the display. """
        self.update_idletasks()
        _left, _top, room_width, room_height = self.screen_area
        width, height = self.winfo_width(), self.winfo_height()
        if self.winfo_reqwidth() > width:
            width = max(width, min(self.winfo_reqwidth(), room_width))
        if self.winfo_reqheight() > height:
            height = max(height, min(self.winfo_reqheight(), room_height))
        window_area.place(self, self.screen_area, width, height)

    def go(self, step):
        """ Navigate to a step when the current application state allows it. """
        state = self.app_state
        if step == "run" and state.run_status == "idle":
            step = "review"
        if state.can_go(step):
            state.left.add(state.step)
            state.step = step
            self.show_screen()
            self.refresh_steps()

    def go_back(self):
        """ Navigate to the previous step. """
        previous = self.app_state.previous_open()
        if previous is not None:
            self.go(previous)

    def go_next(self):
        """ Navigate to the next step. """
        state = self.app_state
        if state.step in ("case", "source", "artifacts"):
            self.go(state.neighbour(1))
        elif state.step == "review":
            self.run_control.start()
        elif state.step == "run" and state.run_status == "running":
            self.run_control.stop()
        elif state.step == "run":
            self.go("results")
        else:
            self.run_control.new_run()

    def close(self):
        """ The window's close button. Closing during a run stops it where it is. """
        if self.app_state.run_status == "running" and not messagebox.askokcancel(
                "Processing still running",
                "A run is still in progress.\n\nClosing now stops it where it is. The report and "
                "the LAVA project will be incomplete, and temporary files may be left behind.\n\n"
                "Close anyway?", icon=messagebox.WARNING, default=messagebox.CANCEL, parent=self):
            return
        self.destroy()

    def watch_unlock(self):
        """ Follow the sequence that opens the source, whatever the screen on show. """
        self.app_state.poll_unlock()
        self.unlock_watch = self.after(UNLOCK_POLL, self.watch_unlock)

    def destroy(self):
        """ Stop following the sequence and the run before the window goes. """
        if self.unlock_watch is not None:
            self.after_cancel(self.unlock_watch)
            self.unlock_watch = None
        self.run_control.stop_watching()
        super().destroy()

    def refresh_steps(self):
        """ Redraw the steps ans status bar after the application state changes. """
        for name in ("steps", "status_bar", "checks"):
            if name in self.widgets:
                self.widgets[name].refresh()

    def focus_field(self, method):
        """ Ask the screen on show to put the cursor in one of its fields, if it has that field. """
        action = getattr(self.widgets.get("screen"), method, None)
        if action is not None:
            action()

    def open_settings(self):
        """ Settings window, not yet available. """
        messagebox.showinfo("Settings", "The Settings window is not built yet.", parent=self)


if __name__ == "__main__":
    check_runtime_dependencies()
    MainWindow().mainloop()
