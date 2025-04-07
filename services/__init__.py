from .amplify import AmplifyService
from .autoscaling import AutoScalingService
from .bedrock import BedrockService
from .config import ConfigService
from .dynamodb import DynamoDBService
from .ec2 import EC2Service
from .fsx import FSxService
from .glue import GlueService
from .iam import IAMService
from .lambda_service import LambdaService
from .lightsail import LightsailService
from .rds import RDSService
from .route53 import Route53Service
from .s3 import S3Service
from .vpc import VPCService

# This is a list of all the services that I have implemented so far.
__all__ = [
    'AmplifyService',
    'AutoScalingService',
    'BedrockService',
    'ConfigService',
    'DynamoDBService',
    'EC2Service',
    'FSxService',
    'GlueService',
    'IAMService',
    'LambdaService',
    'LightsailService',
    'RDSService',
    'Route53Service',
    'S3Service',
    'VPCService'
]