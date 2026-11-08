"""
The Settings window.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from leapp_functions.app import history
from leapp_functions.app.gui import themes
from leapp_functions.app.gui.custom_widgets import GAP, MARGIN, Card, OutlineButton

HISTORY_TEXT = "Enable saving paths as recent history"


class SettingsControl:
    """ Opens the Settings window, and keeps it with the main window while it is open. """

    def __init__(self, app):
        self.app = app
        self.window = None
        app.bind("<Map>", self.on_minimize)
        app.bind("<Unmap>", self.on_minimize)
        app.bind("<Activate>", self.on_activate)

    def opened(self):
        """ The Settings window if it is open. """
        if self.window is not None and self.window.winfo_exists():
            return self.window
        return None

    def open(self):
        """ Open the Settings window, or bring it to the front if it is already open. """
        window = self.opened()
        if window is not None:
            window.lift()
            window.focus_set()
        else:
            self.window = SettingsWindow(self.app)

    def on_minimize(self, event):
        """ The main window has been minimised or brought back: the Settings window follows it. """
        window = self.opened()
        if event.widget is self.app and window is not None:
            window.follow(event.type == tk.EventType.Map)

    def on_activate(self, event):
        """ The system has made the main window the active one when it comes back.
        While the Settings window is open, it is the one that must stay active. """
        window = self.opened()
        if event.widget is self.app and window is not None:
            window.focus_force()


class SettingsWindow(tk.Toplevel):
    """ The settings, in a window of its own above the main one. The main window cannot be used
    while it is open. """

    def __init__(self, app):
        super().__init__(app, bg=app.colors.main_bg)
        self.withdraw()  # hidden while it is built, so that it does not appear in a corner first
        self.app = app
        self.title("Settings")
        self.resizable(False, False)
        self.transient(app)
        themes.title_bar(self, app.appearance.is_dark)

        self.history_enabled = tk.BooleanVar(self, value=history.is_history_enabled())
        self.clear_button = self.build_history()

        close = OutlineButton(self, app, text="Close", command=self.destroy)
        close.pack(anchor="e", padx=MARGIN, pady=(GAP, MARGIN))
        self.bind("<Escape>", lambda _event: self.destroy())
        self.bind("<Map>", self.on_map)

        self.place_over(app)
        self.deiconify()

    def on_map(self, event):
        """ The window is on screen, the first time or after the main window comes back: it takes
        the keyboard and the mouse from the main window again. """
        if event.widget is self:
            self.grab_set()
            self.focus_set()

    def follow(self, shown):
        """ Hide the window while the main window is minimised, show it again when it comes
        back. """
        if shown:
            self.deiconify()
        else:
            self.withdraw()

    def build_history(self):
        """ The card for the history of paths shared by the LEAPPs. Returns its Clear button. """
        card = Card(self, self.app, "HISTORY")
        card.pack(fill="x", padx=MARGIN, pady=(MARGIN, 0))
        ttk.Checkbutton(card.body, text=HISTORY_TEXT, style="Card.TCheckbutton",
                        variable=self.history_enabled,
                        command=self.save_history_enabled).pack(anchor="w", pady=(4, 0))
        button = OutlineButton(card.body, self.app, style="in_card", text="Clear History…",
                               command=self.clear_history)
        button.pack(anchor="w", pady=(GAP, 0))
        button.set_enabled(history.has_history())
        return button

    def save_history_enabled(self):
        """ The check box has been clicked: the setting is saved at once. """
        history.set_history_enabled(self.history_enabled.get())

    def clear_history(self):
        """ Choose which history to clear. """
        messagebox.showinfo("Clear History", "Clearing the history is not built yet.", parent=self)

    def place_over(self, app):
        """ Centre the window over the main window. """
        self.update_idletasks()
        x = app.winfo_rootx() + (app.winfo_width() - self.winfo_reqwidth()) // 2
        y = app.winfo_rooty() + (app.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
