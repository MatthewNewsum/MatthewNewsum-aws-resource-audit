from typing import Dict, List, Any
from botocore.exceptions import ClientError
from .base import AWSService

class DynamoDBService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('dynamodb', region_name=region)
        
    @property
    def service_name(self) -> str:
        return 'dynamodb'

    def audit(self) -> List[Dict[str, Any]]:
        """Audit DynamoDB tables in the region"""
        resources = []
        try:
            paginator = self.client.get_paginator('list_tables')
            for page in paginator.paginate():
                for table_name in page['TableNames']:
                    try:
                        table_details = self._get_table_details(table_name)
                        if table_details:
                            resources.append(table_details)
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'AccessDeniedException':
                            # Return minimal info when access is denied
                            resources.append({
                                'Region': self.region,
                                'Table Name': table_name,
                                'Status': 'ACCESS_DENIED',
                                'Error': str(e)
                            })
                        else:
                            raise
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                print(f"Access denied to list DynamoDB tables in {self.region}")
                # Return empty list but don't fail
                return []
            raise
            
        return resources

    def _get_table_details(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table"""
        try:
            table = self.client.describe_table(TableName=table_name)['Table']
            
            # Build basic info that doesn't require additional API calls
            details = {
                'Region': self.region,
                'Table Name': table['TableName'],
                'ARN': table.get('TableArn', 'N/A'),
                'Status': table.get('TableStatus', 'UNKNOWN'),
                'Creation Time': str(table.get('CreationDateTime', 'N/A')),
                'Item Count': table.get('ItemCount', 0),
                'Size (Bytes)': table.get('TableSizeBytes', 0),
                'Billing Mode': table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED'),
                'Read Capacity': table.get('ProvisionedThroughput', {}).get('ReadCapacityUnits', 'N/A'),
                'Write Capacity': table.get('ProvisionedThroughput', {}).get('WriteCapacityUnits', 'N/A'),
                'Stream Enabled': table.get('StreamSpecification', {}).get('StreamEnabled', False),
                'Encryption Type': table.get('SSEDescription', {}).get('SSEType', 'DEFAULT'),
                'Global Table': bool(table.get('GlobalTableVersion', False)),
                'Tags': '',
                'Point-in-Time Recovery': 'UNKNOWN'
            }

            # Try to get additional details if we have access
            try:
                details['Tags'] = self._get_tags(table.get('TableArn', ''))
            except ClientError:
                pass

            try:
                details['Point-in-Time Recovery'] = self._get_backup_status(table_name)
            except ClientError:
                pass

            return details

        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                print(f"Access denied to describe table {table_name} in {self.region}")
                return None
            raise

    def _get_backup_status(self, table_name: str) -> str:
        try:
            response = self.client.describe_continuous_backups(TableName=table_name)
            return response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus']
        except ClientError:
            return 'UNKNOWN'

    def _get_tags(self, table_arn: str) -> str:
        try:
            tags = self.client.list_tags_of_resource(ResourceArn=table_arn).get('Tags', [])
            return ', '.join([f"{tag['Key']}={tag['Value']}" for tag in tags])
        except ClientError:
            return ''