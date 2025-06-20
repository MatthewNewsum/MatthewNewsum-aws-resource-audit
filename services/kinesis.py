from typing import Dict, List, Any
from .base import AWSService

class KinesisService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('kinesis', region_name=region)
        
    @property
    def service_name(self) -> str:
        return 'kinesis'

    def audit(self) -> List[Dict[str, Any]]:
        """Audit Kinesis resources in the specified region"""
        resources = []
        try:
            # Get Kinesis Data Streams
            try:
                streams = self.client.list_streams()
                for stream_name in streams.get('StreamNames', []):
                    stream_details = self.client.describe_stream(StreamName=stream_name)
                    stream = stream_details['StreamDescription']
                    
                    resources.append({
                        'Region': self.region,
                        'ResourceType': 'Kinesis Data Stream',
                        'ResourceId': stream['StreamName'],
                        'ResourceName': stream['StreamName'],
                        'Status': stream['StreamStatus'],
                        'ShardCount': len(stream.get('Shards', [])),
                        'RetentionPeriod': stream.get('RetentionPeriodHours', 'N/A'),
                        'EncryptionType': stream.get('EncryptionType', 'None')
                    })
            except Exception as e:
                print(f"Error getting Kinesis streams in {self.region}: {str(e)}")
            
            # Get Kinesis Analytics Applications
            try:
                analytics_client = self.session.client('kinesisanalytics', region_name=self.region)
                applications = analytics_client.list_applications()
                for app in applications.get('ApplicationSummaries', []):
                    resources.append({
                        'Region': self.region,
                        'ResourceType': 'Kinesis Analytics Application',
                        'ResourceId': app['ApplicationName'],
                        'ResourceName': app['ApplicationName'],
                        'Status': app['ApplicationStatus']
                    })
            except Exception as e:
                print(f"Error getting Kinesis Analytics applications in {self.region}: {str(e)}")
            
            # Get Kinesis Firehose Delivery Streams
            try:
                firehose_client = self.session.client('firehose', region_name=self.region)
                delivery_streams = firehose_client.list_delivery_streams()
                for stream_name in delivery_streams.get('DeliveryStreamNames', []):
                    stream_details = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
                    stream = stream_details['DeliveryStreamDescription']
                    
                    resources.append({
                        'Region': self.region,
                        'ResourceType': 'Kinesis Firehose Delivery Stream',
                        'ResourceId': stream['DeliveryStreamName'],
                        'ResourceName': stream['DeliveryStreamName'],
                        'Status': stream['DeliveryStreamStatus']
                    })
            except Exception as e:
                print(f"Error getting Kinesis Firehose streams in {self.region}: {str(e)}")
            
            return resources
            
        except Exception as e:
            print(f"Error auditing Kinesis in region {self.region}: {str(e)}")
            return []