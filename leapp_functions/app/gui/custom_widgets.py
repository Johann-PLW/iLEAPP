"""Custom widgets for the new LEAPPs GUI window that Tk does not offer as they are."""

from collections import namedtuple
import tkinter as tk
from tkinter import ttk

from leapp_functions.app.gui import themes


BORDER = 2  # pixels, of an OutlineButton border

# A field of a LabeledEntry: its label, the variable it edits, an example shown while it is
# empty, and whether it is shown in a monospaced font
Field = namedtuple("Field", "label variable example mono", defaults=("", False))


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


class Card(tk.Frame):
    """A panel on the window's background, with a thin border and a small title in capitals.
    What goes in the card is placed in its body, the frame below the title.
    """

    def __init__(self, parent, app, title=""):
        colors = self.colors = app.colors
        # highlightthickness draws a border round a frame, of the colour highlightbackground.
        # While a widget inside has the focus, macOS draws it in highlightcolor instead, which
        # is the colour of the text unless it is given: so both are the border's colour.
        super().__init__(parent, bg=colors.card, highlightthickness=1,
                         highlightbackground=colors.card_border,
                         highlightcolor=colors.card_border)
        inner = tk.Frame(self, bg=colors.card)
        inner.pack(fill="both", expand=True, padx=22, pady=20)
        if title:
            tk.Label(inner, text=title, anchor="w", bg=colors.card, fg=colors.red_text,
                     font=themes.sans(10, "bold")).pack(fill="x", pady=(0, 15))
        self.body = tk.Frame(inner, bg=colors.card)
        self.body.pack(fill="both", expand=True)


class LabeledEntry(tk.Frame):
    """A small label above a field to type in."""

    def __init__(self, parent, app, field):
        colors = self.colors = app.colors
        super().__init__(parent, bg=colors.card)
        self.variable = field.variable
        font = themes.mono(13) if field.mono else themes.sans(13)

        tk.Label(self, text=field.label, anchor="w", bg=colors.card, fg=colors.text_legend,
                 font=themes.sans(10)).grid(row=0, column=0, sticky="ew")

        self.box = tk.Frame(self, bg=colors.input, highlightthickness=1,
                            highlightbackground=colors.input_border,
                            highlightcolor=colors.input_border)
        self.box.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.box.columnconfigure(0, weight=1)
        self.entry = tk.Entry(self.box, textvariable=field.variable, font=font, bg=colors.input,
                              fg=colors.text_primary, insertbackground=colors.text_primary, relief="flat",
                              borderwidth=0, highlightthickness=0)
        self.entry.grid(row=0, column=0, sticky="ew", padx=12, ipady=8)
        self.entry.bind("<FocusIn>", lambda _event: self.set_border(colors.progress))
        self.entry.bind("<FocusOut>", lambda _event: self.set_border(colors.input_border))

        self.example = tk.Label(self.box, text=field.example, anchor="w", bg=colors.input,
                                fg=colors.text_legend, font=font)
        self.example.grid(row=0, column=0, sticky="w", padx=(12, 0))
        self.example.bind("<Button-1>", lambda _event: self.entry.focus_set())

        self.columnconfigure(0, weight=1)
        self.trace = self.variable.trace_add("write", self.show_example)
        self.bind("<Destroy>", self.forget_variable)
        self.show_example()

    def set_border(self, color):
        """Colour the box's border."""
        self.box.configure(highlightbackground=color, highlightcolor=color)

    def show_example(self, *_args):
        """Show the example while the field is empty. Tk calls this when the variable changes."""
        if self.variable.get():
            self.example.grid_remove()
        else:
            self.example.grid()

    def forget_variable(self, event):
        """Stop watching the variable once this widget is gone."""
        if event.widget is self:
            self.variable.trace_remove("write", self.trace)
