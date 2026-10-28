"""Custom widgets for the new LEAPPs GUI window that Tk does not offer as they are."""

from collections import namedtuple
from pathlib import PureWindowsPath
import sys
import tkinter as tk
from tkinter import ttk

from leapp_functions.app.gui import images, themes


BORDER = 2
TOOLTIP_DELAY = 500
TOOLTIP_WIDTH = 520
INFO_SIZE = 14

Field = namedtuple("Field", "label variable mono pick", defaults=(False, None))


BUTTON_STYLES = {"outline": "Primary.TButton", "filled": "Filled.TButton",
                 "quiet": "Quiet.TButton", "in_card": "Field.TButton"}


class OutlineButton(tk.Frame):
    """ A button with a border round it, on the window's background. Its style is one of:
    - "outline": the colour of the header for its border and its text, the default;
    - "filled": the colour of its border for its background instead;
    - "quiet": for the content of a screen: a grey border, no fill;
    - "in_card": for next to the inputs of a card: a grey fill.
    The other options, such as text and command, are those of the ttk.Button inside.
    """
    def __init__(self, parent, app, style="outline", **button_options):
        colors = self.colors = app.colors
        self.border = colors.button_border if style in ("quiet", "in_card") else colors.header_bg
        super().__init__(parent, bg=self.border)
        self.button = ttk.Button(self, style=BUTTON_STYLES[style], **button_options)
        self.button.pack(padx=BORDER, pady=BORDER)

    def set_text(self, text):
        """ Set the text of the button. """
        self.button.configure(text=text)

    def set_enabled(self, enabled):
        """ Let the button be used or not. """
        self.button.state(["!disabled" if enabled else "disabled"])
        self.configure(bg=self.border if enabled else self.colors.line)

    def is_enabled(self):
        """ Whether the button can be used. """
        return self.button.instate(["!disabled"])

    def invoke(self):
        """ Click the button, as the user would. Does nothing if it is disabled."""
        self.button.invoke()


class Tooltip:
    """ Tooltip for inputs with long text. A tooltip that has no text is not shown. """

    def __init__(self, widgets, app, text):
        self.colors = app.colors
        self.text = text
        self.window = None
        self.pending = None
        for widget in widgets:
            widget.bind("<Enter>", lambda _event, widget=widget: self.schedule(widget), add="+")
            # Leaving, clicking and destroying the widget all end the tooltip
            for sequence in ("<Leave>", "<ButtonPress>", "<Destroy>"):
                widget.bind(sequence, lambda _event: self.hide(), add="+")

    def schedule(self, widget):
        """ Show the tooltip under the widget after a short rest of the pointer. """
        self.hide()
        self.pending = (widget, widget.after(TOOLTIP_DELAY, lambda: self.show(widget)))

    def show(self, widget):
        """ Open the window under the widget, unless there is nothing to show. """
        self.pending = None
        text = self.text()
        if not text:
            return
        colors = self.colors
        self.window = tk.Toplevel(widget)
        if sys.platform == "darwin":
            try:
                self.window.tk.call("::tk::unsupported::MacWindowStyle", "style", self.window,
                                    "help", "noShadow")
            except tk.TclError:
                self.window.overrideredirect(True)
        else:
            self.window.overrideredirect(True)
        # Colours reversed: the text's colour for the background and the window's for the text,
        # so that it is not mistaken for a button, an input or a card
        frame = tk.Frame(self.window, bg=colors.text_primary)
        frame.pack()
        tk.Label(frame, text=text, bg=colors.text_primary, fg=colors.main_bg, justify="left",
                 wraplength=TOOLTIP_WIDTH, font=themes.sans(11)).pack(padx=8, pady=5)
        self.window.geometry(
            f"+{widget.winfo_rootx()}+{widget.winfo_rooty() + widget.winfo_height() + 6}")

    def hide(self):
        """ Close the window, or cancel it if it has not appeared yet. """
        if self.pending is not None:
            widget, after_id = self.pending
            widget.after_cancel(after_id)
            self.pending = None
        if self.window is not None:
            self.window.destroy()
            self.window = None


class Card(tk.Frame):
    """A panel on the window's background, with a thin border and a small title in capitals.
    What goes in the card is placed in its body, the frame below the title.
    """

    def __init__(self, parent, app, title=""):
        colors = self.colors = app.colors
        # highlightthickness draws a border round a frame, of the colour highlightbackground.
        # While a widget inside has the focus, macOS draws it in highlightcolor instead, which
        # is the colour of the text unless it is given: so both are the border's colour.
        super().__init__(parent, bg=colors.card_bg, highlightthickness=1,
                         highlightbackground=colors.border,
                         highlightcolor=colors.border)
        inner = tk.Frame(self, bg=colors.card_bg)
        inner.pack(fill="both", expand=True, padx=16, pady=(10, 14))
        if title:
            tk.Label(inner, text=title, anchor="w", bg=colors.card_bg, fg=colors.text_leapp_color,
                     font=themes.sans(10, "bold")).pack(fill="x", pady=(0, 4))
        self.body = tk.Frame(inner, bg=colors.card_bg)
        self.body.pack(fill="both", expand=True)


class LabeledEntry(tk.Frame):
    """A small label above a field to type in."""

    def __init__(self, parent, app, field):
        colors = self.colors = app.colors
        super().__init__(parent, bg=colors.card_bg)
        font = themes.mono(13) if field.mono else themes.sans(13)

        self.title = tk.Frame(self, bg=colors.card_bg)
        self.title.grid(row=0, column=0, sticky="ew")
        tk.Label(self.title, text=field.label, anchor="w", bg=colors.card_bg,
                 fg=colors.text_secondary, font=themes.sans(10)).pack(side="left")

        self.box = tk.Frame(self, bg=colors.input_bg, highlightthickness=1,
                            highlightbackground=colors.line,
                            highlightcolor=colors.line)
        self.box.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.box.columnconfigure(0, weight=1)
        self.entry = tk.Entry(self.box, textvariable=field.variable, font=font, bg=colors.input_bg,
                              fg=colors.text_primary, insertbackground=colors.text_primary, relief="flat",
                              borderwidth=0, highlightthickness=0)
        self.entry.grid(row=0, column=0, sticky="ew", padx=12, ipady=8)
        self.entry.bind("<FocusIn>", lambda _event: self.set_border(colors.border))
        self.entry.bind("<FocusOut>", lambda _event: self.set_border(colors.line))

        self.columnconfigure(0, weight=1)

    def set_border(self, color):
        """Colour the box's border."""
        self.box.configure(highlightbackground=color, highlightcolor=color)


class FileField(tk.Frame):
    """ A LabeledEntry that shows a file's name and cannot be typed in, with a button to pick the file. """

    def __init__(self, parent, app, field):
        colors = app.colors
        super().__init__(parent, bg=colors.card_bg)
        self.labeled = LabeledEntry(self, app, field)
        self.labeled.grid(row=0, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)

        entry = self.labeled.entry
        self.shown = tk.StringVar()
        entry.configure(textvariable=self.shown, state="readonly",
                        readonlybackground=colors.input_bg)

        # The icon after the label says that there is a tooltip.
        self.info = tk.Label(self.labeled.title, bg=colors.card_bg, padx=0, pady=0, borderwidth=0)
        # The line of the label is as high as the icon, with or without it: nothing jumps
        self.labeled.rowconfigure(0, minsize=INFO_SIZE)
        self.info.image = images.load_disc_icon("info-small", INFO_SIZE, colors.text_secondary,
                                               colors.card_bg)
        self.info.configure(image=self.info.image)

        # The entry shows the name only: the tooltip gives the whole path. The pointer on the
        # entry, on its box or on the icon colours the border of the box too.
        hovered = self.hover_widgets()
        self.tooltip = Tooltip(hovered, app, field.variable.get)
        for widget in hovered:
            widget.bind("<Enter>", self.hover, add="+")
            widget.bind("<Leave>", self.hover, add="+")

        self.button = OutlineButton(self, app, command=field.pick, style="in_card")
        self.button.grid(row=0, column=1, padx=(14, 0), sticky="s")

        self.variable = field.variable
        trace = self.variable.trace_add("write", lambda *_args: self.refresh())
        self.bind("<Destroy>", lambda _event: self.variable.trace_remove("write", trace))
        self.refresh()

    def hover_widgets(self):
        """ The widgets that show the tooltip when the pointer is on them. """
        return (self.labeled.box, self.labeled.entry, self.info)

    def hover(self, _event=None):
        """ Colour the border of the box while the pointer is on the field and there is a tooltip to read. """
        under = self.winfo_containing(*self.winfo_pointerxy())
        highlighted = (under in self.hover_widgets() and self.variable.get()) or self.focus_get() is self.labeled.entry
        self.labeled.set_border(self.labeled.colors.border if highlighted else self.labeled.colors.line)

    def refresh(self):
        """ Show the name of the file, and Choose or Change depending on whether one has been picked. """
        path = self.variable.get()
        if path:
            self.info.pack(side="left", padx=(6, 0))
        else:
            self.info.pack_forget()
        # PureWindowsPath reads both / and \ as separators: a path saved on Windows is
        # shown as well on another system
        self.shown.set(PureWindowsPath(path).name)
        self.button.set_text("Change" if path else "Choose")
