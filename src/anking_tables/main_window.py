import os

import aqt
# from aqt import mw
from aqt.webview import AnkiWebView
from bs4 import BeautifulSoup

# PyQt5 and PyQt6 compatibility
try:
    from PyQt5.QtCore import QRegularExpression, QUrl, Qt, QT_VERSION_STR
    from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QIcon, QKeySequence
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QMainWindow, QDockWidget, QDesktopWidget, QFrame, QMessageBox, QShortcut
except (ImportError, AttributeError):
    from PyQt6.QtCore import QRegularExpression, QUrl, Qt, QT_VERSION_STR
    from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QGuiApplication, QIcon, QKeySequence, QShortcut
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QMainWindow, QDockWidget, QFrame, QMessageBox

from .utils import process_table, deheader_first_column, headerize_first_column, parse_html, contains_credits


class HtmlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(HtmlHighlighter, self).__init__(parent)
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#DE3163"))
        keywordPatterns = ["<[^>]*>"]
        self.highlightingRules = [(QRegularExpression(pattern), keywordFormat) for pattern in keywordPatterns]

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class HtmlViewer(QWidget):
    def __init__(self, field_html, card, main_window, col, editor, fieldName, note_id):
        super().__init__()
        self.initial_html = None
        self.webView = None
        self.highlighter = None
        self.htmlEditor = None
        self.field_html, self.original_tables = self.filter_tables(field_html)
        self.card = card
        self.fieldName = fieldName
        self.note_id = note_id
        self.mw = main_window
        self.col = col
        self.editor = editor
        self.initUI(note_id, fieldName)

    def filter_tables(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        original_tables = soup.find_all('table')
        table_strings = []
        for i, table in enumerate(original_tables):
            table_strings.append(str(table))
            if i < len(original_tables) - 1:
                table_strings.append('\n\n<br><!--Table Separator-->\n\n')
        return ''.join(table_strings), original_tables

    def initUI(self, note_id, field_name):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.top_toolbar = TopToolbar(self)
        main_layout.addLayout(self.top_toolbar)

        self.central_widget = CentralWidget(self.editor, self, self.field_html)
        main_layout.addWidget(self.central_widget)

        self.bottom_buttons = BottomButtons(self)
        main_layout.addLayout(self.bottom_buttons)

        self.setLayout(main_layout)
        self.setWindowTitle('Edit Anking Tables')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'edit_tables_gui.png')))
        self.setGeometry(*self.calculate_geometry())
        self.show()

        self.central_widget.htmlEditor.textChanged.connect(self.update_html_viewer)

        self.initial_html = self.central_widget.htmlEditor.toPlainText()
        self.set_html(self.initial_html)

    def set_html(self, html, js_files=None):
        anking_note_type = self.col.models.by_name("AnKingOverhaul (AnKing / AnKingMed)")
        if not anking_note_type:
            print("AnKingOverhaul note type not found")
            return

        anking_css = anking_note_type['css']
        corrected_css = """
        .card {
            padding: 0px;
            margin: 0px;
        }
        .html, td, tr {
            padding: 0px;
            font-size: 22px;
            text-align: center !important;
        }
        .table {
            width: 100%;
        }
        """
        anking_css += corrected_css
        style_tag = f"<style>{anking_css}</style>"
        html = style_tag + html

        self.central_widget.webView.stdHtml(html, css=None, js=js_files, context=self)

    def update_html_viewer(self):
        html = self.central_widget.htmlEditor.toPlainText()
        js_files = ["js/reviewer.js", "js/webview.js"]
        self.set_html(html, js_files)

    def calculate_geometry(self):
        try:
            from PyQt5.QtWidgets import QDesktopWidget
            screen = QDesktopWidget().screenGeometry()
        except ImportError:
            from PyQt6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen().geometry()

        window_width = screen.width() * 0.7
        window_height = screen.height() * 0.7

        left = (screen.width() - window_width) / 2
        top = (screen.height() - window_height) / 2

        return int(left), int(top), int(window_width), int(window_height)


class HtmlEditor(QTextEdit):
    def __init__(self, parent, initial_html):
        super().__init__(parent)
        self.setPlainText(initial_html)
        self.setContentsMargins(20, 20, 20, 20)
        font = QFont()
        font.setPointSize(12.5)
        self.setFont(font)
        self.highlighter = HtmlHighlighter(self.document())

        # Add Ctrl+Z shortcut for undo
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self.undo)

        # Add Ctrl+Y shortcut for redo
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo_shortcut.activated.connect(self.redo)


class TopToolbar(QHBoxLayout):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setContentsMargins(5, 5, 0, 0)
        self.add_toolbar_buttons()

    def add_toolbar_buttons(self):
        buttons = [
            QPushButton(),
            QPushButton(),
        ]
        for i, button in enumerate(buttons):
            button.setFixedSize(25, 25)
            if i == 0:
                button.clicked.connect(lambda: button1_func(self.parent))
                button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'gui_table_1.png')))
                button.setToolTip("Convert to table with a header row ONLY")
            elif i == 1:
                button.clicked.connect(lambda: button2_func(self.parent))
                button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'gui_table_2.png')))
                button.setToolTip("Convert to table with a header row & column")
            self.addWidget(button)
        self.addStretch(1)


class BottomButtons(QHBoxLayout):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.add_buttons()

    def add_buttons(self):
        apply_button = QPushButton("Apply")
        apply_button.setToolTip("Apply changes to selected card")
        apply_button.clicked.connect(lambda: self.parent.central_widget.apply_changes(self.parent.editor, self.parent.mw.col, self.parent.note_id, self.parent.fieldName, self.parent.central_widget.htmlEditor.toPlainText()))

        apply_to_all_button = QPushButton("Apply to All")
        apply_to_all_button.setToolTip("Apply changes to all cards with this table")
        apply_to_all_button.clicked.connect(lambda: self.parent.central_widget.apply_changes_to_all(self.parent.mw.col, self.parent.central_widget.htmlEditor.toPlainText()))
        apply_to_all_button.setEnabled(False)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.parent.close)

        self.addStretch(1)
        self.addWidget(apply_button)
        self.addWidget(apply_to_all_button)
        self.addWidget(cancel_button)


class CentralWidget(QFrame):
    def __init__(self, editor, parent, initial_html):
        super().__init__(parent)
        self.htmlEditor = HtmlEditor(self, initial_html)
        self.webView = AnkiWebView(title="table_editor")
        self.webView.setContentsMargins(0, 0, 0, 0)
        self.editor = editor
        self.parent = parent

        central_layout = QHBoxLayout(self)
        vbox = QVBoxLayout()
        vbox.setContentsMargins(5, 5, 5, 5)
        vbox.addWidget(self.htmlEditor)
        vbox.addWidget(self.webView)

        central_layout.addLayout(vbox, 40)
        central_layout.addWidget(self.webView, 60)
        self.setLayout(central_layout)

    def apply_changes(self, editor, col, note_id, field_name, updated_html):
        note = col.get_note(note_id)

        # Replace the first table in the field with the updated table
        soup = BeautifulSoup(note[field_name], "html.parser")
        tables = soup.find_all("table")
        tables[0].replace_with(BeautifulSoup(updated_html, "html.parser"))

        note[field_name] = str(soup)

        # Save the updated note
        col.update_note(note)

        # Refresh the editor
        self.editor.set_note(note)

        # Check if the note contains photo credit & warn user if it does
        if contains_credits(updated_html):
            msg = QMessageBox()
            if QT_VERSION_STR[0] == "5":
                msg.setIcon(QMessageBox.Warning)
            else:
                msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("This table contains the photo credits, please move them out of the table.\n\n"
                        "All formatting applied to photo credit text has been removed.\n"
                        "You can easily add the proper formatting with the Wrapper meta-addon (use 396502676 to "
                        "download).")
            msg.setWindowTitle("Warning")
            if QT_VERSION_STR[0] == "5":
                msg.exec_()
            else:
                msg.exec()

        # Close the GUI window
        self.parent.close()

    def apply_changes_to_all(self, col, updated_html):
        print("Starting to apply changes to all notes...")

        # Parse the initial HTML and find all tables in it
        original_tables = BeautifulSoup(self.parent.initial_html, "html.parser").find_all("table")

        # Remove <tbody> tags from original tables
        original_tables_html = [str(table).replace("<tbody>", "").replace("</tbody>", "") for table in original_tables]

        # Find all note IDs that contain the original tables
        matched_note_ids = []
        for original_table in original_tables_html:
            print(f"Searching for notes containing the table: {str(original_table)}")
            matched_note_ids.extend(col.find_notes(str(original_table)))
        print(f"Found {len(matched_note_ids)} notes that contain the original tables.")

        # Remove duplicates from the list
        matched_note_ids = list(set(matched_note_ids))
        print(f"Note IDs: {matched_note_ids}")

        # # Iterate over all note IDs for print statements
        # for note_id in matched_note_ids:
        #     # Get the note associated with the current ID
        #     note = col.get_note(note_id)
        #
        #     # Print the field contents of the note
        #     for field_idx, field_content in enumerate(note.fields):
        #         print(f"Note ID: {note_id}, Matched Table(s): {str(original_tables)}")

        # Keep track of updated notes
        updated_notes = []

        # Iterate over all notes
        for note_id in matched_note_ids:
            note = col.get_note(note_id)
            note_updated = False

            # Check all fields for the original tables
            for field_idx, field_content in enumerate(note.fields):
                soup = BeautifulSoup(field_content, "html.parser")
                tables = soup.find_all("table")

                # Remove <tbody> tags from current tables and replace each table that matches any of the original tables
                for table in tables:
                    table_html = str(table).replace("<tbody>", "").replace("</tbody>", "")
                    print(f"Searching for {table_html}")
                    if table_html in original_tables_html:
                        print(f"Found a matching table in note {note_id}, field {field_idx}")
                        print(f"Table of matching note: {table_html}")
                        print(f"Replacing the table with: {str(updated_html)}")
                        table.replace_with(BeautifulSoup(updated_html, "html.parser"))
                        note_updated = True
                    else:
                        print(f"Found no matching table in note {note_id}, field {field_idx}")
                        print(f"Table of unmatched note: {table_html}")

                # Convert the updated BeautifulSoup object back to a string and assign it back to the field
                if note_updated:
                    note.fields[field_idx] = str(soup)
                    print(f"Updated field content: {note.fields[field_idx]}")

            # Save the updated note
            if note_updated:
                col.update_note(note)
                updated_notes.append(note_id)

        print(f"Updated {len(updated_notes)} notes.")

        # Create a filtered browser view with only the updated notes
        browser = aqt.dialogs.open("Browser", self.editor.mw)
        browser.form.searchEdit.lineEdit().setText("nid:" + ",".join(map(str, updated_notes)))
        browser.onSearchActivated()
        print("Filtered browser view created with the updated notes.")

        self.parent.close()


def button1_func(parent):
    html = parent.central_widget.htmlEditor.toPlainText()
    soup = BeautifulSoup(html, 'html.parser')
    for table in soup.find_all('table'):
        process_table(table)
        deheader_first_column(parent.editor, soup)
    new_html = str(soup)
    parent.central_widget.htmlEditor.setPlainText(new_html)
    parent.set_html(new_html)


def button2_func(parent):
    html = parent.central_widget.htmlEditor.toPlainText()
    soup = BeautifulSoup(html, 'html.parser')
    for table in soup.find_all('table'):
        process_table(table)
        headerize_first_column(parent.editor, soup)
    new_html = str(soup)
    parent.central_widget.htmlEditor.setPlainText(new_html)
    parent.set_html(new_html)


# def main(field_html, card, mw, col, editor, fieldName, note_id):
#     app = QApplication.instance()
#     if app is None:
#         app = QApplication([])
#
#     window = HtmlViewer(field_html, card, mw, col, editor, fieldName, note_id)
#     window.show()
#
#     app.exec_()
