"""
The bar at the bottom of the window: what the screen is for, and back and next buttons.
A title and a subtitle on the left say what is expected of the user on this screen. The
subtitle turns red when Next is blocked, and says what is missing.
Back and Next buttons on the right move through the screens in the order of state.ORDER.
The widgets are made once. refresh() changes their texts, their style and their state.
"""

import tkinter as tk

from leapp_functions.app.gui import themes
from leapp_functions.app.gui.custom_widgets import OutlineButton

# For each screen: its title, its subtitle and the text of its main button. The subtitle of
# Artifacts is worked out when it is shown, from the number of artifacts selected.
TEXTS = {
    "case": ("Case data is optional", "It only decorates the header of the report",
             "Continue to Source"),
    "source": ("The extraction and the output folder are required", "The keychain is optional",
               "Continue to Artifacts"),
    "artifacts": ("Choose what to parse", "", "Review and run"),
    "review": ("Ready to run", "The run takes place in the background: the window stays usable",
               "Start parsing"),
    "run": ("Parsing in progress", "Stopping interrupts iLEAPP: the report will be incomplete",
            "Stop"),
    "results": ("Run finished", "The report opens in the default browser", "New run"),
}


class StatusBar(tk.Frame):
    """ The title and subtitle of the screen, and the Back and Next buttons. """

    def __init__(self, parent, app):
        colors = self.colors = app.colors
        super().__init__(parent, bg=colors.main_bg)
        self.app = app

        # A line across the bar, and the room under it, then the texts on the left taking the
        # width left over, then the two buttons.
        tk.Frame(self, height=1, bg=colors.border).grid(row=0, column=0, columnspan=3, sticky="ew")
        self.columnconfigure(0, weight=1)

        texts = tk.Frame(self, bg=colors.main_bg)
        texts.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.title_label = tk.Label(texts, anchor="w", bg=colors.main_bg, fg=colors.text_primary,
                                    font=themes.sans(12, "bold"))
        self.title_label.pack(fill="x")
        self.subtitle_label = tk.Label(texts, anchor="w", bg=colors.main_bg,
                                       font=themes.sans(11))
        self.subtitle_label.pack(fill="x")

        self.back_button = OutlineButton(self, app, text="Back", command=app.go_back)
        self.back_button.grid(row=1, column=1, padx=(16, 0), pady=(8, 0))
        # Next, and in its place on the Run screen the button that stops the run
        self.next_button = OutlineButton(self, app, command=app.go_next, style="filled")
        self.next_button.grid(row=1, column=2, padx=(10, 0), pady=(8, 0))
        self.stop_button = OutlineButton(self, app, command=app.go_next)
        self.stop_button.grid(row=1, column=2, padx=(10, 0), pady=(8, 0))

        self.refresh()

    def refresh(self):
        """ Show the state: the texts of the screen, and which buttons can be used. """
        colors, state = self.colors, self.app.app_state
        title, subtitle, next_text = TEXTS[state.step]
        if state.step == "artifacts":
            subtitle = f"{len(state.selected_artifacts)} artifacts selected"

        # Next is blocked when the screen after this one cannot be reached. Of the screens
        # that move on to another one, only the review can be unreachable.
        target = state.neighbour(1)
        blocked = state.step == "artifacts" and not state.can_go(target)

        self.title_label.configure(text=title)
        self.subtitle_label.configure(
            text=state.missing_for_run() if blocked else subtitle,
            fg=colors.text_leapp_color if blocked else colors.text_legend)

        # Only one of the two is shown. grid_remove() hides a widget and keeps where it was
        # placed, which grid() brings back.
        if state.step == "run":
            self.next_button.grid_remove()
            self.stop_button.grid()
            self.stop_button.set_text(next_text)
        else:
            self.stop_button.grid_remove()
            self.next_button.grid()
            self.next_button.set_text(next_text)
            self.next_button.set_enabled(not blocked)

        # Back goes to the screen before, unless there is none or a run is on
        previous = state.neighbour(-1)
        can_back = (previous is not None and state.run_status != "running"
                    and state.can_go(previous))
        self.back_button.set_enabled(can_back)
