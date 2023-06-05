import json
import boto3
from boto3.dynamodb.conditions import Key

resource = boto3.resource('dynamodb')
table = resource.Table('FinanceParser')


def lambda_handler(event, context):
    query_string_parameters = event['queryStringParameters']
    company_ticker = query_string_parameters['ticker']
    report_type = query_string_parameters['type']
    year = query_string_parameters['year']

    pk = f'{report_type}#{company_ticker}'
    response = table.query(
        KeyConditionExpression=Key('pk').eq(pk) & Key('sk').begins_with(year)
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": {
                "items": response['Items'],
                "count": len(response['Items'])
            }
        }),
    }
