import boto3

ssm = boto3.client('ssm')

def get_ssm_param(name, with_decryption=False):
    response = ssm.get_parameter(Name=name, WithDecryption=with_decryption)
    return response['Parameter']['Value']

