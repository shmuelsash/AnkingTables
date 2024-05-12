import os

from bs4 import BeautifulSoup

from anki.hooks import addHook
from aqt.editor import Editor
from aqt import gui_hooks

def parse_html(editor):
    """Parse the current field's HTML and return a BeautifulSoup object."""
    # Ensure that editor.note and editor.currentField exist
    if editor.note is None or editor.currentField is None:
        return None

    # Get the current field's HTML
    html = editor.note.fields[editor.currentField]

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    return soup

def update_html(editor, soup):
    """Update the current field's HTML with the modified BeautifulSoup object."""
    # Ensure that editor.note and editor.currentField exist
    if editor.note is None or editor.currentField is None:
        return

    # Update the current field's HTML
    editor.note.fields[editor.currentField] = str(soup)
    editor.loadNote()

def on_edit_table(editor):
    """Process the current field's HTML when the EditTable button is clicked."""
    # Get the current field's HTML
    html = editor.note.fields[editor.currentField]

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Process each table in the HTML
    for table in soup.find_all('table'):
        process_table(table)

    # Update the current field's HTML
    editor.note.fields[editor.currentField] = str(soup)
    editor.loadNote()

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

    # Remove all tags that are not 'table', 'tr', 'td', or 'th'
    for tag in table.find_all(True):  # True matches all elements
        if tag.name not in ['table', 'tr', 'td', 'th', 'br', 'b', 'u', 'i', 'ul', 'li', 'ol', 'img', 'sub', 'sup', 'a']:
            tag.unwrap()

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
    update_html(editor, soup)

def headerize_first_column(editor, soup):
    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            first_cell = row.find(['td', 'th'])
            if first_cell and first_cell.name == 'td':
                if not row.find('th'):
                    first_cell.name = 'th'
                    for tag in first_cell.find_all(['b', 'u', 'i']):
                        tag.unwrap()
    update_html(editor, soup)

def button1_func(editor):
    soup = parse_html(editor)
    if soup:
        for table in soup.find_all('table'):
            process_table(table)
        deheader_first_column(editor, soup)

def button2_func(editor):
    soup = parse_html(editor)
    if soup:
        for table in soup.find_all('table'):
            process_table(table)
        headerize_first_column(editor, soup)

def add_buttons(buttons, editor):
    """Add buttons to the editor toolbar."""
    icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'editor_table.png')
    btn1 = editor.addButton(
        icon=icon_path,
        cmd="HeaderRowOnly",
        func=lambda _: button1_func(editor),
        tip="Convert to table with a header row ONLY",
        keys=None,
    )
    buttons.append(btn1)

    icon_path_2 = os.path.join(os.path.dirname(__file__), 'icons', 'editor_table_2.png')
    btn2 = editor.addButton(
        icon=icon_path_2,
        cmd="HeaderColumnRow",
        func=lambda _: button2_func(editor),
        tip="Convert to table with a header row & column",
        keys=None,
    )
    buttons.append(btn2)

gui_hooks.editor_did_init_buttons.append(add_buttons)