"""
The new LEAPPs GUI --> Work in progress.
"""

import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from leapp_functions import leapp
from leapp_functions.app.gui import images, themes
from leapp_functions.app.gui.app_state import AppState
from leapp_functions.app.gui.header import Header
from leapp_functions.app.gui.steps import STAGES, Steps
from leapp_functions.app.gui.case import CaseScreen
from leapp_functions.app.gui.source import SourceScreen
from leapp_functions.app.gui.status_bar import StatusBar

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


SCREENS = {"case": CaseScreen, "source": SourceScreen}


class MainWindow(tk.Tk):
    """ Main application window for the LEAPP GUI. """

    def __init__(self):
        """ Initialize the window, application state, and widgets. """
        super().__init__()
        self.title(f"{leapp.name} version {leapp.version}")
        self.icon = images.load("icon.png")
        self.iconphoto(True, self.icon)
        self.minsize(*MIN_SIZE)

        self.app_state = AppState(self.refresh_steps)
        self.appearance = themes.Appearance(leapp.theme)
        ttk.Style(self).theme_use("clam")

        # Settings
        if sys.platform == "darwin":
            # On macOS: Settings item in the application menu and ⌘,
            self.createcommand("::tk::mac::ShowPreferences", self.open_settings)
        else:
            # Other platforms: Ctrl,
            self.bind_all("<Control-comma>", lambda _event: self.open_settings())

        self.bind("<Control-i>", lambda _event: self.focus_field("focus_input"))
        self.bind("<Control-o>", lambda _event: self.focus_field("focus_output"))

        self.header = None
        self.body_frame = None
        self.widgets = {}
        self.unlock_watch = None

        self.build()
        self.fix_size()
        self.watch_unlock()
        if sys.platform == "darwin":
            # the window has to be on screen first
            self.after(300, self.redraw)

    def fix_size(self):
        """ Give the window the size its first screen asks for """
        self.update_idletasks()
        width = max(self.winfo_reqwidth(), MIN_SIZE[0])
        height = max(self.winfo_reqheight(), MIN_SIZE[1])
        self.geometry(f"{width}x{height}")

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
        for widget in (self.header, self.body_frame):
            if widget is not None:
                widget.destroy()
        self.configure(bg=self.colors.main_bg)
        themes.apply_styles(ttk.Style(self), self.colors)
        if sys.platform == "darwin":
            appearance = "darkaqua" if self.appearance.is_dark else "aqua"
            try:
                self.tk.call("::tk::unsupported::MacWindowStyle", "appearance", self, appearance)
            except tk.TclError:
                pass  # Tk before 8.6.10 has no such setting

        self.header = Header(self, self)
        self.header.pack(fill="x")

        self.body_frame = tk.Frame(self, bg=self.colors.main_bg)
        self.body_frame.pack(fill="both", expand=True, padx=16, pady=(16, 8))
        self.body_frame.columnconfigure(0, weight=1)
        self.body_frame.rowconfigure(1, weight=1)

        self.widgets["steps"] = Steps(self.body_frame, self)
        self.widgets["steps"].grid(row=0, column=0, sticky="ew", pady=(0, 24))

        self.show_screen()

        self.widgets["status_bar"] = StatusBar(self.body_frame, self)
        self.widgets["status_bar"].grid(row=2, column=0, sticky="ew", pady=(16, 8))

    def show_screen(self):
        """ Build the screen of the step. What was typed is in the state, so it survives the screen being rebuilt. """
        old = self.widgets.pop("screen", None)
        if old is not None:
            old.destroy()
        step = self.app_state.step
        screen = SCREENS.get(step, PlaceholderScreen)(self.body_frame, self)
        screen.grid(row=1, column=0, sticky='nsew')
        self.widgets["screen"] = screen
        self.fit_screen()

    def fit_screen(self):
        """ Make the window bigger when the screen on show needs more room than it has, within the
        display. It never gets smaller: a size the user gave it is kept when it is enough. """
        self.update_idletasks()
        width = min(max(self.winfo_width(), self.winfo_reqwidth()), self.winfo_screenwidth())
        height = min(max(self.winfo_height(), self.winfo_reqheight()), self.winfo_screenheight())
        if (width, height) != (self.winfo_width(), self.winfo_height()):
            self.geometry(f"{width}x{height}")

    def go(self, step):
        """ Navigate to a step when the current application state allows it. """
        state = self.app_state
        if step == "run" and state.run_status != "running":
            step = "review"
        if state.can_go(step):
            state.left.add(state.step)
            state.step = step
            self.show_screen()
            self.refresh_steps()

    def go_back(self):
        """ Navigate to the previous step. """
        previous = self.app_state.neighbour(-1)
        if previous is not None:
            self.go(previous)

    def go_next(self):
        """ Navigate to the next step. """
        state = self.app_state
        if state.step in ("case", "source", "artifacts"):
            self.go(state.neighbour(1))
        elif state.step == "results":
            # A new run: what was chosen is kept
            state.run_status = "idle"
            self.go("case")
        else:
            # Starting and stopping a run need the engine, which is not connected yet
            messagebox.showinfo("Not available yet", "The engine is not connected yet.",
                                parent=self)

    def watch_unlock(self):
        """ Follow the sequence that opens the source, whatever the screen on show. """
        self.app_state.poll_unlock()
        self.unlock_watch = self.after(UNLOCK_POLL, self.watch_unlock)

    def destroy(self):
        """ Stop following the sequence before the window goes. """
        if self.unlock_watch is not None:
            self.after_cancel(self.unlock_watch)
            self.unlock_watch = None
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
    MainWindow().mainloop()
