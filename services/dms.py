from typing import Dict, List, Any
from .base import AWSService

class DMSService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('dms', region_name=region)
        
    @property
    def service_name(self) -> str:
        return 'dms'

    def audit(self) -> Dict[str, List[Dict[str, Any]]]:
        try:
            return {
                'replication_instances': self._audit_replication_instances(),
                'replication_tasks': self._audit_replication_tasks(),
                'endpoints': self._audit_endpoints(),
                'replication_subnet_groups': self._audit_replication_subnet_groups()
            }
        except Exception as e:
            print(f"Error auditing DMS in {self.region}: {str(e)}")
            return {
                'replication_instances': [],
                'replication_tasks': [],
                'endpoints': [],
                'replication_subnet_groups': []
            }

    def _audit_replication_instances(self) -> List[Dict[str, Any]]:
        instances = []
        try:
            paginator = self.client.get_paginator('describe_replication_instances')
            for page in paginator.paginate():
                for instance in page.get('ReplicationInstances', []):
                    instances.append({
                        'Region': self.region,
                        'Replication Instance Identifier': instance.get('ReplicationInstanceIdentifier', 'N/A'),
                        'Replication Instance Class': instance.get('ReplicationInstanceClass', 'N/A'),
                        'Replication Instance Status': instance.get('ReplicationInstanceStatus', 'N/A'),
                        'Allocated Storage': instance.get('AllocatedStorage', 'N/A'),
                        'Instance Create Time': str(instance.get('InstanceCreateTime', 'N/A')),
                        'VPC Security Groups': ', '.join([sg.get('VpcSecurityGroupId', '') for sg in instance.get('VpcSecurityGroups', [])]),
                        'Availability Zone': instance.get('AvailabilityZone', 'N/A'),
                        'Subnet Group Identifier': instance.get('ReplicationSubnetGroup', {}).get('ReplicationSubnetGroupIdentifier', 'N/A'),
                        'Publicly Accessible': instance.get('PubliclyAccessible', False),
                        'Multi AZ': instance.get('MultiAZ', False),
                        'Engine Version': instance.get('EngineVersion', 'N/A'),
                        'Auto Minor Version Upgrade': instance.get('AutoMinorVersionUpgrade', False),
                        'Pending Modified Values': str(instance.get('PendingModifiedValues', {})) if instance.get('PendingModifiedValues') else 'None'
                    })
        except Exception as e:
            print(f"Error listing DMS replication instances: {str(e)}")
        return instances

    def _audit_replication_tasks(self) -> List[Dict[str, Any]]:
        tasks = []
        try:
            paginator = self.client.get_paginator('describe_replication_tasks')
            for page in paginator.paginate():
                for task in page.get('ReplicationTasks', []):
                    tasks.append({
                        'Region': self.region,
                        'Replication Task Identifier': task.get('ReplicationTaskIdentifier', 'N/A'),
                        'Replication Task ARN': task.get('ReplicationTaskArn', 'N/A'),
                        'Status': task.get('Status', 'N/A'),
                        'Migration Type': task.get('MigrationType', 'N/A'),
                        'Table Mappings': 'Present' if task.get('TableMappings') else 'None',
                        'Replication Instance ARN': task.get('ReplicationInstanceArn', 'N/A'),
                        'Source Endpoint ARN': task.get('SourceEndpointArn', 'N/A'),
                        'Target Endpoint ARN': task.get('TargetEndpointArn', 'N/A'),
                        'Replication Task Creation Date': str(task.get('ReplicationTaskCreationDate', 'N/A')),
                        'Replication Task Start Date': str(task.get('ReplicationTaskStartDate', 'N/A')),
                        'CDC Start Position': task.get('CdcStartPosition', 'N/A'),
                        'CDC Stop Position': task.get('CdcStopPosition', 'N/A'),
                        'Recovery Checkpoint': task.get('RecoveryCheckpoint', 'N/A'),
                        'Task Data': task.get('TaskData', 'N/A')
                    })
        except Exception as e:
            print(f"Error listing DMS replication tasks: {str(e)}")
        return tasks

    def _audit_endpoints(self) -> List[Dict[str, Any]]:
        endpoints = []
        try:
            paginator = self.client.get_paginator('describe_endpoints')
            for page in paginator.paginate():
                for endpoint in page.get('Endpoints', []):
                    endpoints.append({
                        'Region': self.region,
                        'Endpoint Identifier': endpoint.get('EndpointIdentifier', 'N/A'),
                        'Endpoint Type': endpoint.get('EndpointType', 'N/A'),
                        'Engine Name': endpoint.get('EngineName', 'N/A'),
                        'Username': endpoint.get('Username', 'N/A'),
                        'Server Name': endpoint.get('ServerName', 'N/A'),
                        'Port': endpoint.get('Port', 'N/A'),
                        'Database Name': endpoint.get('DatabaseName', 'N/A'),
                        'Status': endpoint.get('Status', 'N/A'),
                        'KMS Key ID': endpoint.get('KmsKeyId', 'N/A'),
                        'Endpoint ARN': endpoint.get('EndpointArn', 'N/A'),
                        'Certificate ARN': endpoint.get('CertificateArn', 'N/A'),
                        'SSL Mode': endpoint.get('SslMode', 'N/A'),
                        'Service Access Role ARN': endpoint.get('ServiceAccessRoleArn', 'N/A'),
                        'External Table Definition': endpoint.get('ExternalTableDefinition', 'N/A'),
                        'External ID': endpoint.get('ExternalId', 'N/A')
                    })
        except Exception as e:
            print(f"Error listing DMS endpoints: {str(e)}")
        return endpoints

    def _audit_replication_subnet_groups(self) -> List[Dict[str, Any]]:
        subnet_groups = []
        try:
            paginator = self.client.get_paginator('describe_replication_subnet_groups')
            for page in paginator.paginate():
                for subnet_group in page.get('ReplicationSubnetGroups', []):
                    subnet_groups.append({
                        'Region': self.region,
                        'Replication Subnet Group Identifier': subnet_group.get('ReplicationSubnetGroupIdentifier', 'N/A'),
                        'Replication Subnet Group Description': subnet_group.get('ReplicationSubnetGroupDescription', 'N/A'),
                        'VPC ID': subnet_group.get('VpcId', 'N/A'),
                        'Subnet Group Status': subnet_group.get('SubnetGroupStatus', 'N/A'),
                        'Subnets': ', '.join([f"{subnet.get('SubnetIdentifier', '')}({subnet.get('SubnetAvailabilityZone', {}).get('Name', '')})" 
                                            for subnet in subnet_group.get('Subnets', [])]),
                        'Supported Network Types': ', '.join(subnet_group.get('SupportedNetworkTypes', []))
                    })
        except Exception as e:
            print(f"Error listing DMS replication subnet groups: {str(e)}")
        return subnet_groups