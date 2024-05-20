from aqt import mw, dialogs

from bs4 import BeautifulSoup

try:
    from PyQt6.QtCore import QObject, QEvent, Qt
except ImportError:
    from PyQt5.QtCore import QObject, QEvent, Qt


def parse_html(html):
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    return soup


def process_table(table):
    """Process a table element to remove all styling and set the class to 'one' and border to '1'."""
    # Remove all attributes from the table
    table.attrs = {}

    # Set the class of the table to 'one'
    table['class'] = ['one']

    # Set the 'border' attribute of the table to '1'
    table['border'] = '1'

    # Process all elements in the table
    for element in table.find_all(True):  # True matches all elements
        # Preserve colspan and rowspan attributes
        colspan = element.get('colspan')
        rowspan = element.get('rowspan')

        # Preserve src, height, and width attributes for img tags
        src = element.get('src') if element.name == 'img' else None
        height = element.get('height') if element.name == 'img' else None
        width = element.get('width') if element.name == 'img' else None

        # Remove all attributes from the element
        element.attrs = {}

        # Restore colspan and rowspan attributes
        if colspan:
            element['colspan'] = colspan
        if rowspan:
            element['rowspan'] = rowspan

        # Restore src, height, and width attributes for img tags
        if src:
            element['src'] = src
        if height:
            element['height'] = height
        if width:
            element['width'] = width

    # Remove all tags that are not listed
    for tag in table.find_all(True):  # True matches all elements
        if tag.name not in ['table', 'tbody', 'tr', 'td', 'th', 'br', 'b', 'u', 'i', 'ul', 'li', 'ol', 'img', 'sub', 'sup', 'a']:
            tag.unwrap()

    # Convert rows that span across the whole table to td
    for row in table.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        if len(cells) == 1 and cells[0].get('colspan'):  # If the row is merged across the whole table
            # Convert the row to td
            for cell in cells:
                cell.name = 'td'

    # Convert the first row of cells into header cells
    first_row = table.find('tr')
    skip_rows = 1
    if first_row:
        cells = first_row.find_all(['td', 'th'])
        if len(cells) == 1 and cells[0].get('colspan'):  # If the first row is merged across the whole table
            # Treat the second row as the header row
            second_row = first_row.find_next_sibling('tr')
            if second_row:
                for cell in second_row.find_all('td'):
                    cell.name = 'th'
                    # Remove <b>, <u>, and <i> tags from the cell
                    for tag in cell.find_all(['b', 'u', 'i']):
                        tag.unwrap()
            skip_rows = 2
        else:
            for cell in cells:
                cell.name = 'th'
                # Remove <b>, <u>, and <i> tags from the cell
                for tag in cell.find_all(['b', 'u', 'i']):
                    tag.unwrap()
    return skip_rows


def deheader_first_column(editor, soup):
    for table in soup.find_all('table'):
        skip_rows = process_table(table)
        for row in table.find_all('tr')[skip_rows:]:
            first_cell = row.find(['th', 'td'])
            if first_cell:
                first_cell.name = 'td'


def headerize_first_column(editor, soup):
    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            first_cell = row.find(['td', 'th'])
            if first_cell and first_cell.name == 'td':
                # Check if the row spans the entire table
                cells = row.find_all(['td', 'th'])
                if any(cell.get('colspan') for cell in cells):
                    # If the row spans the entire table, skip this row
                    continue
                # Check if the first cell is part of a row span
                previous_row = row.find_previous_sibling('tr')
                if previous_row:
                    previous_row_first_cell = previous_row.find(['td', 'th'])
                    if previous_row_first_cell and previous_row_first_cell.get('rowspan'):
                        # If the first cell is part of a row span, skip this row
                        continue
                if not row.find('th'):
                    first_cell.name = 'th'
                    for tag in first_cell.find_all(['b', 'u', 'i']):
                        tag.unwrap()


def contains_credits(html):
    soup = BeautifulSoup(html, 'html.parser')
    return "Photo credit: " in soup.text


def is_night_mode():
    return "nightMode" in mw.pm.meta["cssState"]


def search_text(text):
    browser = dialogs.open("Browser", mw)
    browser.form.searchEdit.lineEdit().setText(text)
    browser.onSearchActivated()