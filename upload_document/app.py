import json
import boto3


s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('FinanceParser')


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

    for dateColumn, date in doc['dateColumns'].items():
        for row_index, account in doc['data'].items():

            try:
                column_types = account['type']
            except KeyError:
                column_types = []

            """
            Given:
            +------------------+------+------+
            | ASSETS           | 2020 | 2019 |
            +------------------+------+------+
            | ASSETS_ACCOUNT_1 |      |      |
            +------------------+------+------+
            | ASSETS_ACCOUNT_2 |      |      |
            +------------------+------+------+
            
            The following statement avoids getting `2020` as the value of `ASSETS`.
            """

            account_value = account[dateColumn]
            if 'COLUMN_HEADER' in column_types and date == account_value:
                account_value = ''

            with table.batch_writer() as batch:

                # pk -> item_type#company_ticker
                # sk -> date#row_index

                batch.put_item(
                    Item={
                        'pk': f"balance#{event_msg['companyTicker']}",
                        'sk': f'{date}#{row_index}',
                        'account_name': account['1'],
                        'account_value': account_value,
                        'column_types': column_types
                    }
                )

        # pk -> item_type#company_ticker
        # sk -> date#filename

        table.put_item(
            Item={
                'pk': f"file#{event_msg['companyTicker']}",
                'sk': f"{date}#{event_msg['objectKey'].replace('processed/', '')}"
            }
        )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "ok"
        }),
    }
