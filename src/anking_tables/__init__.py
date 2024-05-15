import os
from aqt import mw
from anki import notes
from anki.cards import Card
from anki.collection import Collection

from bs4 import BeautifulSoup

from aqt import gui_hooks
from .main_window import HtmlViewer
from .utils import process_table, deheader_first_column, headerize_first_column, parse_html


try:
    from PyQt6.QtGui import QAction
    from PyQt6.QtWidgets import QMessageBox
except ImportError:
    from PyQt5.QtWidgets import QAction, QMessageBox


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


# def update_html(editor, soup):
#     """Update the current field's HTML with the modified BeautifulSoup object."""
#     # Ensure that editor.note and editor.currentField exist
#     if editor.note is None or editor.currentField is None:
#         return
#
#     # Update the current field's HTML
#     editor.note.fields[editor.currentField] = str(soup)
#     editor.loadNote()


# def on_edit_table(editor):
#     """Process the current field's HTML when the EditTable button is clicked."""
#     # Get the current field's HTML
#     html = editor.note.fields[editor.currentField]
#
#     # Parse the HTML with BeautifulSoup
#     soup = BeautifulSoup(html, 'html.parser')
#
#     # Process each table in the HTML
#     for table in soup.find_all('table'):
#         process_table(table)
#
#     # Update the current field's HTML
#     editor.note.fields[editor.currentField] = str(soup)
#     editor.loadNote()


def add_buttons(buttons, editor):
    """Add buttons to the editor toolbar."""
    # icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'editor_table.png')
    # btn1 = editor.addButton(
    #     icon=icon_path,
    #     cmd="HeaderRowOnly",
    #     func=lambda _: button1_func(editor),
    #     tip="Convert to table with a header row ONLY",
    #     keys=None,
    # )
    # buttons.append(btn1)
    #
    # icon_path_2 = os.path.join(os.path.dirname(__file__), 'icons', 'editor_table_2.png')
    # btn2 = editor.addButton(
    #     icon=icon_path_2,
    #     cmd="HeaderColumnRow",
    #     func=lambda _: button2_func(editor),
    #     tip="Convert to table with a header row & column",
    #     keys=None,
    # )
    # buttons.append(btn2)

    icon_path_3 = os.path.join(os.path.dirname(__file__), 'icons', 'th_td_button_3.png')
    btn3 = editor.addButton(
        icon=icon_path_3,
        cmd="OpenMainWindow",
        func=lambda _: open_main_window_func(editor),
        tip="Open Table Editor",
        keys=None,
    )
    buttons.append(btn3)


gui_hooks.editor_did_init_buttons.append(add_buttons)
