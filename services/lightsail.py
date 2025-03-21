from typing import Dict, List, Any
from .base import AWSService

class LightsailService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('lightsail', region_name=region)
        
    @property
    def service_name(self) -> str:
        return 'lightsail'

    def audit(self) -> List[Dict[str, Any]]:
        resources = []
        try:
            # Get all Lightsail instances
            instances = self.client.get_instances()['instances']
            for instance in instances:
                resources.append({
                    'Region': self.region,
                    'Instance Name': instance['name'],
                    'Instance State': instance['state']['name'],
                    'Availability Zone': instance['location']['availabilityZone'],
                    'Blueprint ID': instance['blueprintId'],
                    'Bundle ID': instance['bundleId'],
                    'Created At': str(instance['createdAt']),
                    'Public IP': instance.get('publicIpAddress', 'N/A'),
                    'Private IP': instance.get('privateIpAddress', 'N/A'),
                    'IPv6 Addresses': ', '.join(instance.get('ipv6Addresses', [])),
                    'Resource Type': 'Instance',
                    'Hardware': f"{instance['hardware']['cpuCount']} vCPU, {instance['hardware']['ramSizeInGb']}GB RAM",
                    'Tags': ', '.join([f"{tag['key']}={tag['value']}" for tag in instance.get('tags', [])])
                })

            # Get all Lightsail databases
            databases = self.client.get_relational_databases()['relationalDatabases']
            for db in databases:
                resources.append({
                    'Region': self.region,
                    'Database Name': db['name'],
                    'Database State': db['state'],
                    'Engine': f"{db['engine']} {db.get('engineVersion', 'N/A')}",
                    'Availability Zone': db['location']['availabilityZone'],
                    'Created At': str(db['createdAt']),
                    'Resource Type': 'Database',
                    'Master Username': db['masterUsername'],
                    'Hardware': db['hardware']['name'],
                    'Storage': f"{db['hardware']['storageSizeInGb']}GB",
                    'Public Access': str(db.get('publiclyAccessible', False)),
                    'Backup Enabled': str(db.get('backupRetentionEnabled', False)),
                    'Tags': ', '.join([f"{tag['key']}={tag['value']}" for tag in db.get('tags', [])])
                })

        except Exception as e:
            print(f"Error auditing Lightsail in {self.region}: {str(e)}")

        return resources