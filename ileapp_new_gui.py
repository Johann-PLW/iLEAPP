"""
The new LEAPPs GUI --> Work in progress.
"""

import sys
import tkinter as tk
from tkinter import messagebox, ttk

from leapp_functions import leapp
from leapp_functions.app.gui import images, themes
from leapp_functions.app.gui.app_state import AppState
from leapp_functions.app.gui.header import Header
from leapp_functions.app.gui.steps import Steps
from leapp_functions.app.gui.status_bar import StatusBar


class MainWindow(tk.Tk):
    """Main application window for the LEAPP GUI."""

    def __init__(self):
        """Initialize the window, application state, and widgets."""
        super().__init__()
        self.title(f"{leapp.name} version {leapp.version}")
        self.icon = images.load("icon.png")
        self.iconphoto(True, self.icon)
        self.minsize(900, 700)

        self.app_state = AppState(self.refresh_steps)
        self.appearance = themes.Appearance(leapp.theme)
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Settings
        if sys.platform == "darwin":
            # On macOS: Settings item in the application menu and ⌘,
            self.createcommand("::tk::mac::ShowPreferences", self.open_settings)
        else:
            # Other platforms: Ctrl,
            self.bind_all("<Control-comma>", lambda _event: self.open_settings())

        self.header = None
        self.body_frame = None
        self.steps = None
        self.status_bar = None

        self.build()

    @property
    def colors(self):
        """ The palette in use """
        return self.appearance.colors

    def build(self):
        """Build or replace every widget using the current palette."""
        for widget in (self.header, self.body_frame):
            if widget is not None:
                widget.destroy()
        self.configure(bg=self.colors.main_bg)
        themes.apply_styles(self.style, self.colors)
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

        self.steps = Steps(self.body_frame, self)
        self.steps.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        self.screen = tk.Frame(self.body_frame, bg="#222222")
        self.screen.grid(row=1, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.body_frame, self)
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=(16, 0))

    def go(self, step):
        """Navigate to a step when the current application state allows it."""
        state = self.app_state
        if step == "run" and state.run_status != "running":
            step = "review"
        if state.can_go(step):
            state.step = step
            self.refresh_steps()

    def go_back(self):
        """Navigate to the previous step."""
        previous = self.app_state.neighbour(-1)
        if previous is not None:
            self.go(previous)

    def go_next(self):
        """Navigate to the next step."""
        state = self.app_state
        if state.step in ("case", "source", "modules"):
            self.go(state.neighbour(1))
        elif state.step == "results":
            # A new run: what was chosen is kept
            state.run_status = "idle"
            self.go("case")
        else:
            # Starting and stopping a run need the engine, which is not connected yet
            messagebox.showinfo("Not available yet", "The engine is not connected yet.",
                                parent=self)

    def refresh_steps(self):
        """Redraw the steps after the application state changes."""
        for widget in (self.steps, self.status_bar):
            if widget is not None:
                widget.refresh()

    def open_settings(self):
        """Settings window, not yet available."""
        messagebox.showinfo("Settings", "The Settings window is not built yet.", parent=self)


if __name__ == "__main__":
    MainWindow().mainloop()
