import json
import boto3
import uuid
import re


textract_client = boto3.client('textract')
s3_client = boto3.client('s3')


def lambda_handler(event, context):
    event_detail = event['detail']
    bucket_name = event_detail['bucket']['name']
    object_key = event_detail['object']['key']
    company_ticker = re.search('unprocessed/(.*).pdf', object_key).group(1)

    data_dict = textract_client.analyze_document(
        Document={'S3Object': {'Bucket': bucket_name, 'Name': object_key}},
        FeatureTypes=['TABLES']
    )

    data_string = json.dumps(data_dict, indent=2, default=str)
    filename = f'{company_ticker}_{uuid.uuid4()}.json'

    s3_client.put_object(
        Bucket=bucket_name,
        Key=f'analyzed/{filename}',
        Body=data_string
    )

    s3_client.delete_object(
        Bucket=bucket_name,
        Key=object_key
    )

    return {
        "statusCode": 200,
        "body": {
            "message": {
                "objectKey": f'analyzed/{filename}',
                "bucketName": bucket_name
            }
        },
    }
