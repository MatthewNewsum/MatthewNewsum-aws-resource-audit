from typing import Dict, List, Any
from .base import AWSService

class RDSService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('rds', region_name=region)
        
    @property
    def service_name(self) -> str:
        return 'rds'

    def audit(self) -> List[Dict[str, Any]]:
        resources = []
        
        try:
            paginator = self.client.get_paginator('describe_db_instances')
            for page in paginator.paginate():
                for db in page.get('DBInstances', []):
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