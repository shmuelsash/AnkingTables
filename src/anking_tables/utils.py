from bs4 import BeautifulSoup


def parse_html(html):
    """Parse the current field's HTML and return a BeautifulSoup object."""
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


def headerize_first_column(editor, soup):
    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            first_cell = row.find(['td', 'th'])
            if first_cell and first_cell.name == 'td':
                if not row.find('th'):
                    first_cell.name = 'th'
                    for tag in first_cell.find_all(['b', 'u', 'i']):
                        tag.unwrap()