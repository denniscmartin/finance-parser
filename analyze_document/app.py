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

    company_ticker = re.search('unprocessed/(.*)_', object_key).group(1)
    doc_type = re.search(f'unprocessed/{company_ticker}_(.*).pdf', object_key).group(1)
    file_id = uuid.uuid4()

    data_dict = textract_client.analyze_document(
        Document={'S3Object': {'Bucket': bucket_name, 'Name': object_key}},
        FeatureTypes=['TABLES']
    )

    data_string = json.dumps(data_dict, indent=2, default=str)
    filename = f'{company_ticker}_{doc_type}_{file_id}.json'

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
                "companyTicker": company_ticker,
                "docType": doc_type,
                "fileId": file_id,
                "fileName": filename,
                "objectKey": f'analyzed/{filename}',
                "bucketName": bucket_name
            }
        },
    }
