import json
import boto3
from datetime import datetime
from collections import defaultdict


s3_client = boto3.client('s3')


def lambda_handler(event, context):
    event_msg = event['body']['message']

    # Download file from s3
    s3_client.download_file(
        event_msg['bucketName'],
        event_msg['objectKey'],
        '/tmp/document.json'
    )

    with open('/tmp/document.json') as f:
        doc = json.load(f)

    # Analyze document
    result = defaultdict(dict)
    blocks = doc['Blocks']

    # Get format
    lines = filter_blocks(blocks, 'BlockType', 'LINE')
    for line in lines:
        amount_format = get_format(line['Text'])
        result['format'] = amount_format
        if amount_format:
            break

    # Find dates value and position
    data = defaultdict(dict)
    cells = filter_blocks(blocks, 'BlockType', 'CELL')
    for cell in cells:
        if not 'Relationships' in cell:
            continue

        child_ids = [r['Ids'] for r in cell['Relationships'] if r['Type'] == 'CHILD'][0]

        # Get `Text` from `CELL` block
        cell_text = ''
        for index, child_id in enumerate(child_ids):
            word_block = filter_blocks(blocks, 'Id', child_id)[0]
            cell_text += word_block['Text']

            if index < len(child_ids) - 1:
                cell_text += '_'

        # Verify if `Text` could be a valid date
        date_string = is_date(cell_text)
        if date_string:
            cell_text = date_string
            result['dateRow'] = cell['RowIndex']
            result['dateColumns'][cell['ColumnIndex']] = date_string

        cell_row_index = cell['RowIndex']
        cell_column_index = cell['ColumnIndex']
        data[cell_row_index][cell_column_index] = clean_text(cell_text)

        try:
            data[cell_row_index]['type'] = cell['EntityTypes']
        except KeyError:
            pass

    # Delete unused row and columns
    for row_index in list(data.keys()):
        row = data[row_index]
        for column_index in list(row.keys()):
            if column_index not in result['dateColumns'] \
                    and column_index != 1 and column_index != 'type':
                del row[column_index]

            if len(row) > 1:
                result['data'][row_index] = row

    object_key = event_msg['objectKey'].replace('analyzed/', 'processed/')
    data_string = json.dumps(result, indent=2, default=str)

    s3_client.put_object(
        Bucket=event_msg['bucketName'],
        Key=object_key,
        Body=data_string
    )

    return {
        "statusCode": 200,
        "body": {
            "message": {
                "companyTicker": event_msg['companyTicker'],
                "docType": event_msg['docType'],
                "fileId": event_msg['fileId'],
                "fileName": event_msg['fileName'],
                "objectKey": object_key,
                "bucketName": event_msg['bucketName']
            }
        },
    }


def filter_blocks(blocks, block_key, block_value):
    """
    Extract a block by key-value from array of blocks
    """

    return [block for block in blocks if block[block_key] == block_value]


def is_date(string_date):
    """
    Verify if a string could be a date.
    """

    formats_allowed = ['%d-%m-%Y', '%d/%m/%Y', '%Y']

    for format_allowed in formats_allowed:
        try:
            date = datetime.strptime(string_date, format_allowed)

            if date.year > datetime.now().year or date.year < 1900:
                return  # Fecha fuera de rango

            return date.strftime("%Y")
        except ValueError:

            # Try removing characters from the beginning and end
            options = [string_date[:-1], string_date[1:], string_date[1:-1]]
            for option in options:
                try:
                    date = datetime.strptime(option, format_allowed)

                    if date.year > datetime.now().year or date.year < 1900:
                        return  # Fecha fuera de rango

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

        if amount_format in phrase.lower() or plural_amount_format in phrase.lower():
            return amount_format


def clean_text(text, text_type='default'):
    """"
    Remove bad characters from word
    """

    special_chars = [
        '!', '@', '#', '$', '%', '^', '&', '*', '(', ')',
        '-', '_', '+', '=', '[', ']', '{', '}', '\\', '|',
        ';', ':', '"', '\'', '<', '>', '/', '?', '.', ','
    ]

    if text_type == 'date':
        allowed_chars = ['_', '-', '/']
    else:
        allowed_chars = ['_']

    special_chars = [char for char in special_chars if char not in allowed_chars]

    for char in special_chars:
        text = text.replace(char, '')

    return text.lower()
