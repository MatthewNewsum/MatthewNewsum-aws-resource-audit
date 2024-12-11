from typing import Dict, List, Any
from .base import AWSService

class DynamoDBService(AWSService):
    @property
    def service_name(self) -> str:
        return 'dynamodb'

    def audit(self) -> List[Dict[str, Any]]:
        resources = []
        paginator = self.client.get_paginator('list_tables')
        
        for page in paginator.paginate():
            for table_name in page['TableNames']:
                table_details = self._get_table_details(table_name)
                if table_details:
                    resources.append(table_details)
                    
        return resources

    def _get_table_details(self, table_name: str) -> Dict[str, Any]:
        try:
            table = self.client.describe_table(TableName=table_name)['Table']
            tags = self.client.list_tags_of_resource(ResourceArn=table['TableArn'])
            backup_status = self._get_backup_status(table_name)
            
            return {
                'Region': self.region,
                'Table Name': table['TableName'],
                'ARN': table['TableArn'],
                'Status': table['TableStatus'],
                'Creation Time': str(table['CreationDateTime']),
                'Item Count': table.get('ItemCount', 0),
                'Size (Bytes)': table.get('TableSizeBytes', 0),
                'Billing Mode': table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED'),
                'Read Capacity': table.get('ProvisionedThroughput', {}).get('ReadCapacityUnits', 'N/A'),
                'Write Capacity': table.get('ProvisionedThroughput', {}).get('WriteCapacityUnits', 'N/A'),
                'Point-in-Time Recovery': backup_status,
                'Stream Enabled': table.get('StreamSpecification', {}).get('StreamEnabled', False),
                'Encryption Type': table.get('SSEDescription', {}).get('SSEType', 'N/A'),
                'Global Table': bool(table.get('GlobalTableVersion', False)),
                'Tags': self._format_tags(tags.get('Tags', []))
            }
        except Exception as e:
            print(f"Error processing table {table_name}: {str(e)}")
            return None

    def _get_backup_status(self, table_name: str) -> str:
        try:
            response = self.client.describe_continuous_backups(TableName=table_name)
            return response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus']
        except:
            return 'DISABLED'

    def _format_tags(self, tags: List[Dict[str, str]]) -> str:
        return ', '.join([f"{tag['Key']}={tag['Value']}" for tag in tags])