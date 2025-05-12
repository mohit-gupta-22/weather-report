import boto3
import json
from botocore.exceptions import ClientError
import base64

def get_secret(secret_name, region_name="ap-south-1"):
    client = boto3.client('secretsmanager', region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            secret = response['SecretString']
        else:
            secret = base64.b64decode(response['SecretBinary']).decode('utf-8')
        return json.loads(secret)
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise
