import json
from datetime import datetime


def main():
    with open('santander.json') as f:
        doc = json.load(f)
    
    if doc['JobStatus'] != 'SUCCEEDED':
        print(f"JOB STATUS: {doc['JobStatus']}")

        return

    blocks = doc['Blocks']
    table = extract_block(blocks, 'BlockType', 'TABLE')
    table_child_ids = extract_child_ids(table)
    
    for table_child_id in table_child_ids:
        cell = extract_block(blocks, 'Id', table_child_id)
        cell_child_ids = extract_child_ids(cell)
        
        cell_value = ''
        for index, cell_child_id in enumerate(cell_child_ids):
            word_block = extract_block(blocks, 'Id', cell_child_id)
            cell_value += word_block['Text'].lower()

            if index < len(cell_child_ids) - 1:
                cell_value += '_'
        
        print(cell_value)
        print(is_date(cell_value))



def extract_child_ids(block):
    if not 'Relationships' in block:
        return []
    
    return [r['Ids'] for r in block['Relationships'] if r['Type'] == 'CHILD'][0]


def extract_block(blocks, block_key, block_value):
    return [block for block in blocks if block[block_key] == block_value][0]


def is_date(string_date):
    formats_allowed = ['%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y']

    for format_allowed in formats_allowed:
        try:
            datetime.strptime(string_date, format_allowed)

            return True
        except ValueError:

            # Try removing characters from the beginning and end
            options = [string_date[:-1], string_date[1:], string_date[1:-1]]
            for option in options:
                try:
                    datetime.strptime(option, format_allowed)

                    return True
                except ValueError:
                    continue
    
    return False


if __name__ == '__main__':
    main()