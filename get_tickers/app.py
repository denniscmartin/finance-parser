import json
import boto3
from boto3.dynamodb.conditions import Key

resource = boto3.resource('dynamodb')
table = resource.Table('FinanceParser')


def lambda_handler(event, context):
    response = table.scan(
        FilterExpression=Key('pk').begins_with('file')
    )

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET"
        },
        "body": json.dumps({
            "message": {
                "items": response['Items'],
                "count": len(response['Items'])
            }
        }),
    }
