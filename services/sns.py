import boto3
from typing import Dict, List, Any
from .base import AWSService

class SNSService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = self.get_client('sns')
        
    @property
    def service_name(self) -> str:
        return 'sns'

    def audit(self) -> List[Dict[str, Any]]:
        resources = []
        try:
            paginator = self.client.get_paginator('list_topics')
            for page in paginator.paginate():
                for topic in page.get('Topics', []):
                    resources.append({
                        'Region': self.region,
                        'Topic ARN': topic['TopicArn'],
                        'Topic Name': topic['TopicArn'].split(':')[-1]
                    })
                    
        except Exception as e:
            print(f"Error listing SNS topics in {self.region}: {str(e)}")
            
        return resources