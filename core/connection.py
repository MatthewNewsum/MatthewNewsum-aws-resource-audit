import boto3
from botocore.exceptions import ClientError
from utils.exceptions import AuthenticationError

def check_aws_connection():
    try:
        session = boto3.Session()
        sts = session.client('sts')
        sts.get_caller_identity()
        return True
    except ClientError as e:
        raise AuthenticationError(f"AWS Connection Error: {e}")