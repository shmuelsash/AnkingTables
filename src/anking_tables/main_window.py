import os

import aqt
from aqt import mw
from aqt.webview import AnkiWebView
from bs4 import BeautifulSoup

# PyQt5 and PyQt6 compatibility
try:
    from PyQt5.QtCore import QRegularExpression, QUrl, Qt, QT_VERSION_STR
    from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QIcon
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QMainWindow, QDockWidget, QDesktopWidget, QFrame, QMessageBox
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
except (ImportError, AttributeError):
    from PyQt6.QtCore import QRegularExpression, QUrl, Qt, QT_VERSION_STR
    from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QGuiApplication, QIcon
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QMainWindow, QDockWidget, QFrame, QMessageBox

from .utils import process_table, deheader_first_column, headerize_first_column, parse_html, contains_credits


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.html_viewer = None
        self.inspector_dock = None
        self.initUI()
        self.show()

    def initUI(self):
        # Create an instance of the HtmlViewer
        self.html_viewer = HtmlViewer("", None, self, col)

        self.setCentralWidget(self.html_viewer)
        self.setWindowTitle("Table Editor")


class HtmlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(HtmlHighlighter, self).__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#DE3163"))

        keywordPatterns = ["<[^>]*>"]

        self.highlightingRules = [(QRegularExpression(pattern), keywordFormat)
                                  for pattern in keywordPatterns]

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
            # Add separator only if there is a next table (currently any field with > 1 table is not supported)
            if i < len(original_tables) - 1:
                table_strings.append('\n\n<br><!--Table Separator-->\n\n')
        return ''.join(table_strings), original_tables

    def initUI(self, note_id, field_name):
        # Layouts
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Top Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 5, 0, 0)
        toolbar_buttons = [
            QPushButton(),
            QPushButton(),
        ]
        for i, button in enumerate(toolbar_buttons):
            button.setFixedSize(25, 25)
            if i == 0:
                button.clicked.connect(lambda: button1_func(self))
                button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'gui_table_1.png')))
                button.setToolTip("Convert to table with a header row ONLY")
            elif i == 1:
                button.clicked.connect(lambda: button2_func(self))
                button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'gui_table_2.png')))
                button.setToolTip("Convert to table with a header row & column")
            toolbar.addWidget(button)
        toolbar.addStretch(1)
        main_layout.addLayout(toolbar)

        # Central Widgets
        central_widget = QFrame(self)

        if QT_VERSION_STR[0] == "5":
            central_widget.setFrameShape(QFrame.StyledPanel)
            central_widget.setFrameShadow(QFrame.Raised)
        elif QT_VERSION_STR[0] == "6":
            central_widget.setFrameShape(QFrame.Shape.StyledPanel)
            central_widget.setFrameShadow(QFrame.Shadow.Raised)

        central_widget.setStyleSheet("border-radius: 10px;")

        central_layout = QHBoxLayout(central_widget)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(5, 5, 5, 5)

        # Text Edit for HTML
        self.htmlEditor = QTextEdit()
        self.htmlEditor.setPlainText(self.field_html)
        self.htmlEditor.setContentsMargins(20, 20, 20, 20)
        vbox.addWidget(self.htmlEditor)
        font = QFont()
        font.setPointSize(12.5)
        self.htmlEditor.setFont(font)

        # Apply the syntax highlighter to the QTextEdit widget
        self.highlighter = HtmlHighlighter(self.htmlEditor.document())

        # Web View to display HTML
        self.webView = AnkiWebView(title="table_editor")
        self.webView.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.webView)

        central_layout.addLayout(vbox, 40)
        central_layout.addWidget(self.webView, 60)

        main_layout.addWidget(central_widget)

        # Bottom Buttons
        bottom_buttons = QHBoxLayout()

        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(
            lambda: self.apply_changes(mw.col, note_id, field_name, self.htmlEditor.toPlainText()))

        apply_to_all_button = QPushButton("Apply to All")
        apply_to_all_button.clicked.connect(
            lambda: self.apply_changes_to_all(mw.col, self.htmlEditor.toPlainText()))

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)

        bottom_buttons.addWidget(apply_button)
        bottom_buttons.addWidget(apply_to_all_button)
        bottom_buttons.addWidget(cancel_button)
        main_layout.addLayout(bottom_buttons)

        def calculate_geometry(self):
            # Get screen size
            try:
                from PyQt5.QtWidgets import QDesktopWidget
                screen = QDesktopWidget().screenGeometry()
            except ImportError:
                from PyQt6.QtGui import QGuiApplication
                screen = QGuiApplication.primaryScreen().geometry()

            # Set window size to 80% of the screen size
            window_width = screen.width() * 0.7
            window_height = screen.height() * 0.7

            # Calculate the position of the window to center it on the screen
            left = (screen.width() - window_width) / 2
            top = (screen.height() - window_height) / 2

            return int(left), int(top), int(window_width), int(window_height)

        self.setLayout(main_layout)
        self.setWindowTitle('Edit Anking Tables')
        self.setGeometry(*calculate_geometry(self))
        self.show()

        # Connect text changes to the update function
        self.htmlEditor.textChanged.connect(self.update_html_viewer)

        # Set initial HTML content
        self.initial_html = self.htmlEditor.toPlainText()
        print(f"initial_html has been updated to: {self.initial_html}")
        self.set_html(self.initial_html)

    def set_html(self, html, js_files=None):
        # Access the Anki model by name; ensure 'self.col' is your collection instance
        anking_note_type = self.col.models.by_name("AnKingOverhaul (AnKing / AnKingMed)")
        if not anking_note_type:
            print("AnKingOverhaul note type not found")
            return

        # Get the CSS from the AnKingOverhaul note type
        anking_css = anking_note_type['css']

        # Fix padding and margin issues
        corrected_css = """
        .card {
            padding: 0px;
            margin: 0px;
        }
        .html {
            padding: 0px;
            font-size: 20px;
        }
        .table {
            width: 100%;
        }
        """

        # Append the corrected CSS to the AnKingOverhaul CSS
        anking_css += corrected_css

        # Create a style tag with the CSS content
        style_tag = f"<style>{anking_css}</style>"

        # Inject the style tag into the HTML content
        html = style_tag + html

        # Use your web view's method to display HTML with CSS and JS
        # This assumes 'self.webView' has a method like 'stdHtml' to set the content
        # Make sure to adjust 'stdHtml' to suit how your web view accepts parameters
        self.webView.stdHtml(html, css=None, js=js_files, context=self)

    def update_html_viewer(self):
        html = self.htmlEditor.toPlainText()
        js_files = ["js/reviewer.js", "js/webview.js"]
        self.set_html(html, js_files)

    def apply_changes(self, col, note_id, field_name, updated_html):
        # Get the note associated with the card
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
        if contains_credits(note[field_name]):
            msg = QMessageBox()
            if QT_VERSION_STR[0] == "5":
                msg.setIcon(QMessageBox.Warning)
            else:
                msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("This table contains the photo credits, please move them out of the table.\n\n"
                        "All formatting applied to photo credit text has been removed.\n"
                        "You can easily add the proper formatting with the Wrapper meta-addon (use 396502676 to download).")
            msg.setWindowTitle("Warning")
            if QT_VERSION_STR[0] == "5":
                msg.exec_()
            else:
                msg.exec()

        # Close the HtmlViewer window
        self.close()

    # def apply_changes_to_all(self, col, original_tables, updated_html):
    #     #print(f"Searching for notes in the collection...")
    #     # Get all note IDs in the collection
    #     note_ids = col.find_notes("")
    #     print(f"Found {len(note_ids)} notes in the collection.")
    #     print(f"Original tables: {original_tables}")
    #     print(f"Updated HTML: {updated_html}")
    #     # Keep track of updated notes
    #     updated_notes = []
    #
    #     # Iterate over all notes
    #     for note_id in note_ids:
    #         #print(f"Processing note with ID: {note_id}")
    #         note = col.get_note(note_id)
    #
    #         # Check all fields for the original tables
    #         any_table_found = False
    #         for field_content in note.values():
    #             soup = BeautifulSoup(field_content, "html.parser")
    #             for original_table in original_tables:
    #                 original_table_str = str(original_table)  # Convert to string
    #                 original_table_soup = BeautifulSoup(original_table_str, "html.parser")
    #                 tables = soup.find_all(str(original_table_soup.table))
    #                 if tables:
    #                     print(f"Found {len(tables)} instance(s) of the original table in this note.")
    #                     # Replace the original table with the updated table
    #                     for table in tables:
    #                         table.replace_with(BeautifulSoup(updated_html, "html.parser"))
    #
    #                     any_table_found = True
    #
    #         if any_table_found:
    #             # Save the updated note
    #             # col.update_note(note)  # Comment out this line
    #
    #             # Add the note ID to the list of updated notes
    #             updated_notes.append(note_id)
    #             print(f"Note with ID {note_id} marked for update.")
    #         #else:
    #         #    print(f"No instances of the original table found in any field of the note.")
    #
    #     print(f"Found {len(updated_notes)} notes to update.")
    #
    #     # Create a filtered browser view with only the updated notes
    #     browser = aqt.dialogs.open("Browser", self.editor.mw)
    #     browser.form.searchEdit.lineEdit().setText("nid:" + ",".join(map(str, updated_notes)))
    #     browser.onSearchActivated()
    #     print("Filtered browser view created with the notes marked for update.")

    # def apply_changes_to_all(self, col, original_tables, updated_html):
    #     # Find all note IDs that contain the original tables
    #     nid_list = []
    #     for original_table in original_tables:
    #         original_table_str = str(original_table)
    #         nid_list.extend(col.find_notes(f'"{original_table_str}"'))
    #
    #         # If no notes were found, strip HTML tags and search again
    #         if not nid_list:
    #             soup = BeautifulSoup(original_table_str, "html.parser")
    #             text_only = soup.get_text(separator=" ")
    #             print(f"original_table: {original_table_str}")  # Debugging line
    #             print(f"text_only: {text_only}")  # Debugging line
    #             escaped_text_only = escape_search_text(text_only)
    #             print(f"escaped_text_only: {escaped_text_only}")  # Debugging line
    #             nid_list.extend(col.find_notes(f'"{escaped_text_only}"'))
    #
    #     # Remove duplicates from the list
    #     nid_list = list(set(nid_list))
    #     print(f"Original tables: {original_tables}")
    #     print(f"Updated HTML: {updated_html}")
    #     print(f"Found {len(nid_list)} notes containing the original table(s).")
    #     print(f"Note IDs: {nid_list}")
    #
    #     # Keep track of updated notes
    #     updated_notes = []
    #
    #     # Iterate over the notes containing the original tables
    #     for note_id in nid_list:
    #         note = col.get_note(note_id)
    #         any_field_updated = False
    #
    #         # Check all fields for the original tables
    #         for field_idx, field_content in enumerate(note.fields):
    #             print(f"Searching in field index {field_idx} with content: {field_content}")
    #             new_field_content = field_content
    #             for original_table in original_tables:
    #                 print(f"Searching for original table: {original_table}")
    #                 new_field_content = new_field_content.replace(str(original_table), updated_html)
    #
    #             if new_field_content != field_content:
    #                 note.fields[field_idx] = new_field_content
    #                 any_field_updated = True
    #
    #         if any_field_updated:
    #             # Save the updated note
    #             col.update_note(note)
    #
    #             # Add the note ID to the list of updated notes
    #             updated_notes.append(note_id)
    #             print(f"Note with ID {note_id} updated.")
    #         else:
    #             print(f"No instances of the original table found in any field of the note with ID {note_id}.")
    #
    #     print(f"Found {len(updated_notes)} notes to update.")
    #
    #     # Create a filtered browser view with only the updated notes
    #     browser = aqt.dialogs.open("Browser", self.editor.mw)
    #     browser.form.searchEdit.lineEdit().setText("nid:" + ",".join(map(str, updated_notes)))
    #     browser.onSearchActivated()
    #     print("Filtered browser view created with the notes marked for update.")

    def apply_changes_to_all(self, col, updated_html):
        print("Starting to apply changes to all notes...")

        # Parse the initial HTML and find all tables in it
        original_tables = BeautifulSoup(self.initial_html, "html.parser").find_all("table")

        # Find all note IDs that contain the original tables
        note_ids = []
        for original_table in original_tables:
            print(f"Searching for notes containing the table: {str(original_table)}")
            note_ids.extend(col.find_notes(str(original_table)))
        print(f"Found {len(note_ids)} notes that contain the original tables.")
        # Remove duplicates from the list
        note_ids = list(set(note_ids))
        print(f"Note IDs: {note_ids}")

        # Iterate over all note IDs
        for note_id in note_ids:
            # Get the note associated with the current ID
            note = col.get_note(note_id)

            # Print the field contents of the note
            for field_idx, field_content in enumerate(note.fields):
                print(f"Note ID: {note_id}, Field Index: {field_idx}, Field Content: {field_content}")


        # Keep track of updated notes
        updated_notes = []

        # Iterate over all notes
        for note_id in note_ids:
            note = col.get_note(note_id)
            any_field_updated = False

            # Check all fields for the original tables
            for field_idx, field_content in enumerate(note.fields):
                soup = BeautifulSoup(field_content, "html.parser")
                tables = soup.find_all("table")

                # Replace each table that matches any of the original tables
                for table in tables:
                    for original_table in original_tables:
                        if str(table) == str(original_table):
                            print(f"Found a matching table in note {note_id}, field {field_idx}")
                            print(f"Field content of matching note: {field_content}")
                            print(f"Soup of matching note: {soup}")
                            print(f"Replacing the table with: {str(updated_html)}")
                            table.replace_with(BeautifulSoup(updated_html, "html.parser"))
                            any_field_updated = True

                # Convert the updated BeautifulSoup object back to a string and assign it back to the field
                if any_field_updated:
                    note.fields[field_idx] = str(soup)
                    print(f"Updated field content: {note.fields[field_idx]}")

            # Save the updated note if any field was updated
            if any_field_updated:
                col.update_note(note)
                updated_notes.append(note_id)
                print(f"Updated note with ID: {note_id}")

        print(f"Updated a total of {len(updated_notes)} notes.")

        # Create a filtered browser view with only the updated notes
        browser = aqt.dialogs.open("Browser", self.editor.mw)
        browser.form.searchEdit.lineEdit().setText("nid:" + ",".join(map(str, updated_notes)))
        browser.onSearchActivated()
        print("Filtered browser view created with the updated notes.")

        # Close the GUI window
        self.close()


def button1_func(self):
    html = self.htmlEditor.toPlainText()
    soup = parse_html(html)
    if soup:
        for table in soup.find_all('table'):
            process_table(table)
        deheader_first_column(self.editor, soup)
    new_html = str(soup)
    self.htmlEditor.setPlainText(new_html)
    self.set_html(new_html)


def button2_func(self):
    html = self.htmlEditor.toPlainText()
    soup = parse_html(html)
    if soup:
        for table in soup.find_all('table'):
            process_table(table)
        headerize_first_column(self.editor, soup)
    new_html = str(soup)
    self.htmlEditor.setPlainText(new_html)
    self.set_html(new_html)

# if __name__ == '__main__':
#     app = QApplication(sys.argv)

#     mw = MainWindow()
#     viewer = HtmlViewer("", None, mw)
#     sys.exit(app.exec())
