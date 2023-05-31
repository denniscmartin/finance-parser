import json
from datetime import datetime
from collections import defaultdict


def main():
    data = defaultdict(dict)
    date_index = defaultdict(dict)

    with open('santander.json') as f:
        doc = json.load(f)
    
    if doc['JobStatus'] != 'SUCCEEDED':
        print(f"JOB STATUS: {doc['JobStatus']}")

        return

    blocks = doc['Blocks']

    # Get format
    lines = filter_blocks(blocks, 'BlockType', 'LINE')
    for line in lines:
        format = get_format(line['Text'])
        data['format'] = format
        if format:
            break

    # Find dates value and position
    cells = filter_blocks(blocks, 'BlockType', 'CELL')
    for cell in cells:
        child_ids = extract_child_ids(cell)
        
        # Get `Text` from `CELL` block
        cell_text = ''
        for index, child_id in enumerate(child_ids):
            word_block = filter_blocks(blocks, 'Id', child_id)[0]
            cell_text += word_block['Text']

        date_string = is_date(cell_text)
        if date_string:
            cell_text = date_string
            date_index[date_string]['column'] = cell['ColumnIndex']
            date_index[date_string]['row'] = cell['RowIndex']


        cell_row_index = cell['RowIndex']
        cell_column_index = cell['ColumnIndex']
        data['rows'][cell_row_index][cell_column_index] = cell_text

    # Delete unused rows
    for year in date_index:
        for row in data['rows']:
            print(row)
            exit()
            if year[row] < row:
                del data[row]

    print(data)

    

        

    print(data)



    """ 
    # Get table
    table = filter_blocks(blocks, 'BlockType', 'TABLE')[0]
    table_child_ids = extract_child_ids(table)

    # Iterate over childs and get `CELL` blocks
    for table_child_id in table_child_ids:
        cell = filter_blocks(blocks, 'Id', table_child_id)[0]
        cell_child_ids = extract_child_ids(cell)

        # Get `Text` from `CELL` block
        cell_text = ''
        for cell_child_id in cell_child_ids:
            word_block = filter_blocks(blocks, 'Id', cell_child_id)[0]
            cell_text += word_block['Text']

        # Check if cell_text could be a date
        date_string = is_date(cell_text)
        if date_string:
            date_column_index = cell['ColumnIndex']
            data[date_column_index] = {'year': date_string}
    """
         

def filter_blocks(blocks, block_key, block_value):
    """
    Extract a block by key-value from array of blocks
    """

    return [block for block in blocks if block[block_key] == block_value]


def extract_child_ids(block):
    """
    Extract child Ids from a block
    """

    if not 'Relationships' in block:
        return []
    
    return [r['Ids'] for r in block['Relationships'] if r['Type'] == 'CHILD'][0]


def is_date(string_date):
    """
    Verify if a string could be a date
    """

    formats_allowed = ['%d-%m-%Y', '%d_%m_%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y']

    for format_allowed in formats_allowed:
        try:
            date = datetime.strptime(string_date, format_allowed)

            return date.strftime("%Y")
        except ValueError:

            # Try removing characters from the beginning and end
            options = [string_date[:-1], string_date[1:], string_date[1:-1]]
            for option in options:
                try:
                    date = datetime.strptime(option, format_allowed)

                    return date.strftime("%Y")
                except ValueError:
                    continue
    
    return 


def get_format(phrase):
    """
    Given a phrase verify if it is specified the amount format
    """

    amount_formats = ['thousand', 'million', 'billion']

    for amount_format in amount_formats:
        plural_amount_format = f'{amount_format}s'

        if amount_format in phrase or plural_amount_format in phrase:
            return amount_format


def clean(string_type, string):
    characters = ['.', ',', '-', ' ']

    clean_string = string
    for character in characters:
        clean_string = clean_string.replace(character, '')

    return clean_string
         

def format_amount(string_amount):
    pass


if __name__ == '__main__':
    main()

"""
Assumptions:
- Thousand separator is `,`
- Supported date formats '%d-%m-%Y', '%d_%m_%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y'
- Accounting values are in the same column and below the date.
+-------+-------+
| 2022  | 2023  |
+-------+-------+
| 3,000 | 3,100 |
+-------+-------+
|  120  |  150  |
+-------+-------+
|  789  |  800  |
+-------+-------+
- Account names must be in column index 1
"""