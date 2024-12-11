from typing import Dict, List, Any
from .base import AWSService

class S3Service(AWSService):
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
        resources = []
        buckets = self.client.list_buckets()['Buckets']
        
        for bucket in buckets:
            try:
                location = self.client.get_bucket_location(Bucket=bucket['Name'])
                region = location['LocationConstraint'] or 'us-east-1'
                
                bucket_info = self._get_bucket_info(bucket['Name'])
                metrics = self.get_bucket_metrics(bucket['Name'])
                
                bucket_info.update({
                    'BucketName': bucket['Name'],
                    'CreationDate': str(bucket['CreationDate']),
                    'Region': region,
                    'Size': metrics['BucketSizeBytes'],
                    'ObjectCount': metrics['NumberOfObjects']
                })
                
                resources.append(bucket_info)
                
            except Exception as e:
                print(f"Error processing bucket {bucket['Name']}: {str(e)}")
                
        return resources

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