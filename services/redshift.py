from typing import Dict, List, Any
from .base import AWSService

class RedshiftService(AWSService):
    @property
    def service_name(self) -> str:
        return 'redshift'

    def audit(self) -> List[Dict[str, Any]]:
        resources = []
        try:
            paginator = self.client.get_paginator('describe_clusters')
            for page in paginator.paginate():
                for cluster in page['Clusters']:
                    resources.append({
                        'Region': self.region,
                        'Cluster ID': cluster['ClusterIdentifier'],
                        'Status': cluster['ClusterStatus'],
                        'Node Type': cluster['NodeType'],
                        'Node Count': cluster['NumberOfNodes'],
                        'DB Name': cluster['DBName'],
                        'Master Username': cluster['MasterUsername'],
                        'Endpoint': f"{cluster['Endpoint']['Address']}:{cluster['Endpoint']['Port']}",
                        'VPC ID': cluster.get('VpcId', 'N/A'),
                        'Cluster Version': cluster.get('ClusterVersion', 'N/A'),
                        'Encrypted': cluster.get('Encrypted', False),
                        'Public Access': cluster.get('PubliclyAccessible', False),
                        'Availability Zone': cluster.get('AvailabilityZone', 'N/A'),
                        'Created At': str(cluster.get('ClusterCreateTime', 'N/A')),
                        'Tags': ', '.join([f"{tag['Key']}={tag['Value']}" for tag in cluster.get('Tags', [])])
                    })
        except Exception as e:
            print(f"Error auditing Redshift in {self.region}: {str(e)}")
        return resources