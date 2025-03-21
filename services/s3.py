from typing import Dict, List, Any
from .base import AWSService

class S3Service(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        # S3 is a global service, so we don't need a region
        self.client = session.client('s3')
        
    @property
    def service_name(self) -> str:
        return 's3'
    
    def get_bucket_metrics(self, bucket_name: str) -> Dict[str, str]:
        results = {
            'BucketSizeBytes': 'N/A',
            'NumberOfObjects': 'N/A'
        }
        
        try:
            total_size = 0
            total_objects = 0
            paginator = self.client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj.get('Size', 0)
                        total_objects += 1
            
            if total_size > 0:
                size_str = self._format_size(total_size)
                results['BucketSizeBytes'] = size_str
                results['NumberOfObjects'] = f"{total_objects:,}"
                    
        except Exception as e:
            print(f"Error getting metrics for bucket {bucket_name}: {str(e)}")
        
        return results

    def _format_size(self, size: int) -> str:
        for unit in ['TB', 'GB', 'MB', 'KB']:
            if size >= 1024**4 and unit == 'TB':
                return f"{size / (1024**4):.2f} TB"
            elif size >= 1024**3 and unit == 'GB':
                return f"{size / (1024**3):.2f} GB"
            elif size >= 1024**2 and unit == 'MB':
                return f"{size / (1024**2):.2f} MB"
        return f"{size / 1024:.2f} KB"

    def audit(self) -> List[Dict[str, Any]]:
        buckets = []
        try:
            response = self.client.list_buckets()
            for bucket in response['Buckets']:
                bucket_details = {
                    'Name': bucket['Name'],
                    'CreationDate': str(bucket['CreationDate'])
                }
                
                try:
                    location = self.client.get_bucket_location(Bucket=bucket['Name'])
                    bucket_details['Region'] = location.get('LocationConstraint', 'us-east-1')
                except Exception as e:
                    bucket_details['Region'] = f'Error getting location: {str(e)}'
                
                buckets.append(bucket_details)
                
        except Exception as e:
            print(f"Error listing S3 buckets: {str(e)}")
            
        return buckets

    def _get_bucket_info(self, bucket_name: str) -> Dict[str, Any]:
        info = {}
        
        try:
            versioning = self.client.get_bucket_versioning(Bucket=bucket_name)
            info['Versioning'] = versioning.get('Status', 'Disabled')
        except:
            info['Versioning'] = 'Unknown'
        
        try:
            encryption = self.client.get_bucket_encryption(Bucket=bucket_name)
            info['EncryptionEnabled'] = True
            info['EncryptionType'] = encryption['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
        except:
            info['EncryptionEnabled'] = False
            info['EncryptionType'] = 'None'
            
        return info