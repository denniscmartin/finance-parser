import json
import boto3
from boto3.dynamodb.conditions import Key

resource = boto3.resource('dynamodb')
table = resource.Table('FinanceParser')


def lambda_handler(event, context):
    response = table.scan(
        FilterExpression=Key('pk').begins_with('file')
    )

    results = []
    for item in response['Items']:
        item_pk = item['pk'].split('#', 1)[1]
        item_year = item['sk'].split('#', 1)[0]
        item_key = f'{item_pk}#{item_year}'  # pnl#acx#2022

        if item_key not in results:
            results.append(item_key)

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET"
        },
        "body": json.dumps({
            "message": {
                "items": results,
                "count": len(results)
            }
        }),
    }
