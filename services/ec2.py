from typing import Dict, List, Any
from .base import AWSService
import boto3

class EC2Service(AWSService):
    def __init__(self, session: boto3.Session, region: str = None):
        super().__init__(session, region)
        self.client = self.get_client('ec2')

    @property
    def service_name(self) -> str:
        return 'ec2'
    
    def get_eip_map(self) -> Dict[str, Dict]:
        try:
            eips = self.client.describe_addresses()['Addresses']
            return {eip.get('InstanceId'): eip for eip in eips if eip.get('InstanceId')}
        except Exception:
            return {}

    def audit(self) -> List[Dict[str, Any]]:
        resources = []
        eip_map = self.get_eip_map()
        
        paginator = self.client.get_paginator('describe_instances')
        for page in paginator.paginate():
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    eip_info = eip_map.get(instance['InstanceId'], {})
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    resources.append({
                        'Region': self.region,
                        'Instance ID': instance['InstanceId'],
                        'Name': tags.get('Name', 'N/A'),
                        'State': instance['State']['Name'],
                        'Instance Type': instance['InstanceType'],
                        'Platform': instance.get('Platform', 'linux'),
                        'Private IP': instance.get('PrivateIpAddress', 'N/A'),
                        'Public IP': instance.get('PublicIpAddress', 'N/A'),
                        'Elastic IP': eip_info.get('PublicIp', 'N/A'),
                        'EIP Allocation ID': eip_info.get('AllocationId', 'N/A'),
                        'VPC ID': instance.get('VpcId', 'N/A'),
                        'Subnet ID': instance.get('SubnetId', 'N/A'),
                        'Key Name': instance.get('KeyName', 'N/A'),
                        'Launch Time': str(instance.get('LaunchTime', 'N/A')),
                        'Security Groups': ', '.join([sg['GroupId'] for sg in instance.get('SecurityGroups', [])]),
                        'Environment': tags.get('Environment', 'N/A'),
                        'Owner': tags.get('Owner', 'N/A'),
                        'Cost Center': tags.get('CostCenter', 'N/A')
                    })
        
        return resources