from typing import Dict, List, Any
from .base import AWSService

class RDSService(AWSService):
    @property
    def service_name(self) -> str:
        return 'rds'

    def audit(self) -> List[Dict[str, Any]]:
        resources = []
        
        try:
            for db in self.client.describe_db_instances()['DBInstances']:
                resources.append({
                    'Region': self.region,
                    'DB Identifier': db['DBInstanceIdentifier'],
                    'Status': db['DBInstanceStatus'],
                    'Engine': f"{db['Engine']} {db['EngineVersion']}",
                    'Instance Class': db['DBInstanceClass'],
                    'Storage': f"{db['AllocatedStorage']} GB",
                    'Storage Type': db['StorageType'],
                    'Multi-AZ': db.get('MultiAZ', False),
                    'Endpoint': db.get('Endpoint', {}).get('Address', 'N/A'),
                    'Port': db.get('Endpoint', {}).get('Port', 'N/A'),
                    'VPC ID': db.get('DBSubnetGroup', {}).get('VpcId', 'N/A'),
                    'Publicly Accessible': db.get('PubliclyAccessible', False)
                })
        except Exception as e:
            print(f"Error auditing RDS in {self.region}: {str(e)}")
            
        return resources