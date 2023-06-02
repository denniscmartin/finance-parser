import json
import boto3
import re

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('FinanceParser')


def lambda_handler(event, context):
    event_message = event['body']['message']
    object_key = event_message['objectKey']
    bucket_name = event_message['bucketName']
    company_ticker = re.search('processed/(.*)_', object_key).group(1)

    # Download file from s3
    s3_client.download_file(bucket_name, object_key, '/tmp/document.json')

    with open('/tmp/document.json') as f:
        doc = json.load(f)

    for dateColumn, date in doc['dateColumns'].items():
        for row_index, account in doc['data'].items():

            try:
                column_types = account['type']
            except KeyError:
                column_types = []

            """
            The following statement avoids getting a `2020` as the value 
            of `ASSETS`.
            
            +------------------+------+------+
            | ASSETS           | 2020 | 2019 |
            +------------------+------+------+
            | ASSETS_ACCOUNT_1 |      |      |
            +------------------+------+------+
            | ASSETS_ACCOUNT_2 |      |      |
            +------------------+------+------+
            """

            account_value = account[dateColumn]
            if 'COLUMN_HEADER' in column_types and date == account_value:
                account_value = ''

            with table.batch_writer() as batch:

                # pk -> item_type#company_ticker
                # sk -> date#row_index

                batch.put_item(
                    Item={
                        'pk': f'balance#{company_ticker}',
                        'sk': f'{date}#{row_index}',
                        'account_name': account['1'],
                        'account_value': account_value,
                        'column_types': column_types
                    }
                )

        # pk -> item_type#company_ticker
        # sk -> date

        table.put_item(
            Item={
                'pk': f'file#{company_ticker}',
                'sk': f"{date}",
                'filename': object_key.replace('processed/', '')
            }
        )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "ok"
        }),
    }
