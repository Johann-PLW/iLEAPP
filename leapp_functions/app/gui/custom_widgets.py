"""Custom widgets for the new LEAPPs GUI window that Tk does not offer as they are."""

import tkinter as tk
from tkinter import ttk

BORDER = 2  # pixels, of an OutlineButton border


class OutlineButton(tk.Frame):
    """A button with a border round it, on the window's background."""
    def __init__(self, parent, app, text="", command=None):
        colors = self.colors = app.colors
        super().__init__(parent, bg=colors.progress)
        self.button = ttk.Button(self, text=text, command=command, style="Primary.TButton")
        self.button.pack(padx=BORDER, pady=BORDER)

    def set_text(self, text):
        """Change the text of the button."""
        self.button.configure(text=text)

    def set_enabled(self, enabled):
        """Let the button be used or not. A button that cannot be has a grey border."""
        self.button.state(["!disabled" if enabled else "disabled"])
        self.configure(bg=self.colors.progress if enabled else self.colors.line)

    def is_enabled(self):
        """Whether the button can be used."""
        return self.button.instate(["!disabled"])

    def invoke(self):
        """Click the button, as the user would. Does nothing if it is disabled."""
        self.button.invoke()
