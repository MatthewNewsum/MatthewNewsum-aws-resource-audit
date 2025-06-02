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
            # Get Topics
            paginator = self.client.get_paginator('list_topics')
            for page in paginator.paginate():
                for topic in page.get('Topics', []):
                    topic_arn = topic['TopicArn']
                    topic_name = topic_arn.split(':')[-1]
                    
                    # Get subscriptions for this topic
                    subs_paginator = self.client.get_paginator('list_subscriptions_by_topic')
                    subscriptions = []
                    try:
                        for subs_page in subs_paginator.paginate(TopicArn=topic_arn):
                            for sub in subs_page.get('Subscriptions', []):
                                subscriptions.append({
                                    'Subscription ARN': sub['SubscriptionArn'],
                                    'Protocol': sub['Protocol'],
                                    'Endpoint': sub['Endpoint']
                                })
                    except Exception as e:
                        print(f"Error listing subscriptions for topic {topic_arn} in {self.region}: {str(e)}")

                    resources.append({
                        'Region': self.region,
                        'Topic ARN': topic_arn,
                        'Topic Name': topic_name,
                        'Subscriptions': subscriptions,
                        'Subscription Count': len(subscriptions)
                    })
                    
        except Exception as e:
            print(f"Error listing SNS topics in {self.region}: {str(e)}")
            
        return resources