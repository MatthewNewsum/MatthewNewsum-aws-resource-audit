from .amplify import AmplifyService
from .autoscaling import AutoScalingService
from .bedrock import BedrockService
from .dynamodb import DynamoDBService
from .ec2 import EC2Service
from .glue import GlueService
from .iam import IAMService
from .lambda_service import LambdaService
from .lightsail import LightsailService
from .rds import RDSService
from .route53 import Route53Service
from .s3 import S3Service
from .vpc import VPCService

# This is a list of all the services that we have implemented so far.
__all__ = [
    'AmplifyService',
    'AutoScalingService',
    'BedrockService',
    'DynamoDBService',
    'EC2Service',
    'GlueService',
    'IAMService',
    'LambdaService',
    'LightsailService',
    'RDSService',
    'Route53Service',
    'S3Service',
    'VPCService'
]