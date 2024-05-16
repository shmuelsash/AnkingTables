import os

from aqt import gui_hooks, mw
from bs4 import BeautifulSoup
try:
    from PyQt6.QtGui import QAction
    from PyQt6.QtWidgets import QMessageBox
except ImportError:
    from PyQt5.QtWidgets import QAction, QMessageBox

from .main_window import HtmlViewer
from .utils import process_table, deheader_first_column, headerize_first_column, parse_html


def open_main_window_func(editor):
    # Get the note object associated with the current card
    note = editor.note

    # Get the HTML content of the current field
    field_html = note.fields[editor.currentField]

    # Get the field name & card id of the selected field
    note_id = note.id
    field_name = note.note_type()['flds'][editor.currentField]['name']

    card = editor.card

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(field_html, 'html.parser')

    # Check if there are any tables in the HTML
    tables = soup.find_all('table')
    if not tables:
        # If there are no tables, show an error message and return
        QMessageBox.critical(None, "Error",
                             "There are no tables in this field, please place the cursor in the field of the table "
                             "you would like to edit.")
        return
    elif len(tables) > 1:
        # If there are multiple tables, show an error message and return
        QMessageBox.critical(None, "Error",
                             "This addon is currently unable to handle fields with multiple tables in it.")
        return

    # Pass thingies (idk how to code so idk what it's called) to the HtmlViewer
    viewer = HtmlViewer(field_html, card, mw, mw.col, editor, field_name, note_id)

    # Store the HtmlViewer object in the Editor object
    editor.html_viewer = viewer
    viewer.show()


def add_buttons(buttons, editor):
    icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'edit_tables.png')
    btn = editor.addButton(
        icon=icon_path,
        cmd="OpenMainWindow",
        func=lambda _: open_main_window_func(editor),
        tip="Open Table Editor",
        keys=None,
    )
    buttons.append(btn)


gui_hooks.editor_did_init_buttons.append(add_buttons)
