from .amplify import AmplifyService
from .bedrock import BedrockService
from .dynamodb import DynamoDBService
from .ec2 import EC2Service
from .iam import IAMService
from .lambda_service import LambdaService
from .rds import RDSService
from .s3 import S3Service
from .vpc import VPCService

# This is a list of all the services that we have implemented so far.
__all__ = [
    'AmplifyService',
    'BedrockService',
    'DynamoDBService',
    'EC2Service',
    'IAMService',
    'LambdaService',
    'RDSService',
    'S3Service',
    'VPCService'
]