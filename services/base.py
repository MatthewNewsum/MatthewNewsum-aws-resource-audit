from abc import ABC, abstractmethod
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

class AWSService:
    def __init__(self, session: boto3.Session, region: str = None):
        self.session = session
        self.region = region
        
    def get_client(self, service_name: str):
        try:
            # For global services (like IAM, S3), don't require region
            if service_name in ['iam', 's3']:
                return self.session.client(service_name)
            # For regional services, always use the region
            return self.session.client(service_name, region_name=self.region)
        except Exception as e:
            print(f"Error creating client for {service_name} in region {self.region}: {str(e)}")
            raise