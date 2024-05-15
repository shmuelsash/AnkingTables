import sys
import os
import aqt
from aqt import mw
import logging

from aqt.webview import AnkiWebView
from anki.collection import Collection
from bs4 import BeautifulSoup

from .utils import process_table, deheader_first_column, headerize_first_column, parse_html


# Conditional imports for PyQt5 and PyQt6 compatibility
try:
    from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QMainWindow,
                                 QDockWidget, QDesktopWidget, QFrame)
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
    from PyQt5.QtCore import QUrl, Qt, QT_VERSION_STR
    from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QIcon
    from PyQt5.QtCore import QRegularExpression
    from PyQt5.Qt import PYQT_VERSION_STR

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
except (ImportError, AttributeError):
    from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QMainWindow,
                                 QDockWidget, QFrame)
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtCore import QUrl, Qt, QT_VERSION_STR
    from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QGuiApplication, QIcon
    from PyQt6.QtCore import QRegularExpression

    app = QApplication(sys.argv)


# os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"
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

        # # Resize the main window to a larger size
        # self.resize(1200, 800)

        # # Create an instance of the InspectorDockWidget
        # self.inspector_dock = InspectorDockWidget(self)
        # # Add the inspector dock widget to the main window
        # self.addDockWidget(Qt.RightDockWidgetArea, self.inspector_dock)
        # # Set the inspected page to the web view's page
        # self.inspector_dock.setInspectedPage(self.html_viewer.webView.page())


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


# class InspectorDockWidget(QDockWidget):
#     def __init__(self, parent=None):
#         super().__init__("Inspector", parent)
#         self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
#
#         # Create a QWebEngineView to serve as the inspector
#         self.inspector = QWebEngineView(self)
#         self.setWidget(self.inspector)
#
#     def setInspectedPage(self, page):
#         self.inspector.page().setInspectedPage(page)


class HtmlViewer(QWidget):
    def __init__(self, field_html, card, main_window, col, editor, fieldName, note_id):
        super().__init__()
        self.webView = None
        self.highlighter = None
        self.htmlEditor = None
        self.field_html = self.filter_tables(field_html)
        self.card = card
        self.fieldName = fieldName
        self.note_id = note_id
        self.mw = main_window
        self.col = col
        self.editor = editor
        self.initUI(note_id, fieldName)

    def filter_tables(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        table_strings = []
        for i, table in enumerate(tables):
            table_strings.append(str(table))
            # Add separator only if there is a next table (currently any field with > 1 table is not supported)
            if i < len(tables) - 1:
                table_strings.append('\n\n<br><!--Table Separator-->\n\n')
        return ''.join(table_strings)

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
                button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'editor_table.png')))
                button.setToolTip("Convert to table with a header row ONLY")
            elif i == 1:
                button.clicked.connect(lambda: button2_func(self))
                button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'editor_table_2.png')))
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

        # def resizeEvent(self, event):
        #     new_width = event.size().width()
        #     new_font_size = new_width * 0.02
        #     font = QFont()
        #     self.setPointSize(new_font_size)
        #     self.htmlEditor.setFont(font)
        #     super().resizeEvent(event)

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
        apply_button.clicked.connect(lambda: self.apply_changes(mw.col, note_id, field_name, self.htmlEditor.toPlainText()))

        apply_to_all_button = QPushButton("Apply to All")

        cancel_button = QPushButton("Cancel")

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
        self.htmlEditor.textChanged.connect(self.update_html)

        # Set initial HTML content
        initial_html = self.htmlEditor.toPlainText()
        self.set_html(initial_html)

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

    def update_html(self):
        html = self.htmlEditor.toPlainText()
        js_files = ["js/reviewer.js", "js/webview.js"]  # Example list of JavaScript files
        self.set_html(html, js_files)

    def apply_changes(self, col, note_id, field_name, updated_html):
        # Get the note associated with the card
        note = col.get_note(note_id)

        print(f"Before update: {note[field_name]}")

        # Replace the first table in the field with the updated table
        soup = BeautifulSoup(note[field_name], "html.parser")
        tables = soup.find_all("table")
        tables[0].replace_with(BeautifulSoup(updated_html, "html.parser"))

        note[field_name] = str(soup)

        print(f"After update: {note[field_name]}")

        # Save the updated note
        col.update_note(note)  # This will save the changes to the database

        # Refresh the editor
        self.editor.set_note(note)

        # Close the HtmlViewer window
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