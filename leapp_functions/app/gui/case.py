"""The Case screen: the data of the case, which only decorates the header of the report."""

import tkinter as tk

from leapp_functions.app.gui.custom_widgets import Card, Field, LabeledEntry

SIDE_WIDTH = 292  # pixels, of the column on the right
GAP = 14          # pixels between two cards, and between two fields of a card


class CaseScreen(tk.Frame):
    """The fields of the Case screen, which edit the variables of the window's state."""

    def __init__(self, parent, app):
        colors = app.colors
        state = app.app_state
        super().__init__(parent, bg=colors.main_bg)

        # The cards take the width left over; the column on the right has a width of its own.
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, minsize=SIDE_WIDTH)

        main = tk.Frame(self, bg=colors.main_bg)
        main.grid(row=0, column=0, sticky="new")
        main.columnconfigure(0, weight=1)

        # Each card has two fields side by side: the first of a minimum width, both growing with
        # the window, the second twice as fast. A card with a single field and no width gives
        # that field the whole width.
        # The agency card will get its logo field next to its name.
        cards = (
            ("CASE", None, (
                Field("Case number", state.case.number, True),)),
            ("AGENCY", 300, (
                Field("Agency / unit", state.case.agency),)),
            ("EXAMINER", 200, (
                Field("Examiner", state.case.examiner),
                Field("Notes", state.case.notes))),
        )
        for row, (title, first_width, fields) in enumerate(cards):
            card = Card(main, app, title)
            card.grid(row=row, column=0, sticky="ew", pady=(0 if row == 0 else GAP, 0))
            if first_width is None:
                card.body.columnconfigure(0, weight=1)
            else:
                card.body.columnconfigure(0, minsize=first_width,
                                          weight=1 if len(fields) > 1 else 0)
                card.body.columnconfigure(1, weight=2)
            for column, field in enumerate(fields):
                entry = LabeledEntry(card.body, app, field)
                entry.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else GAP, 0))
