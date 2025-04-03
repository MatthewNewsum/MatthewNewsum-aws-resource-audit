import boto3
from typing import List, Dict, Any
from services.base import AWSService

class FSxService(AWSService):
    """Service class for Amazon FSx"""

    def __init__(self, session, region=None):
        """Initialize the FSx service client.
        
        Args:
            session: boto3 session
            region: AWS region (optional)
        """
        super().__init__(session)
        self.client = self.session.client('fsx', region_name=region)
        self.region = region or self.session.region_name
        
    def audit(self) -> List[Dict[str, Any]]:
        """Audit FSx resources in the current region"""
        resources = []
        
        # Get all file systems
        try:
            paginator = self.client.get_paginator('describe_file_systems')
            for page in paginator.paginate():
                for fs in page.get('FileSystems', []):
                    # Extract tags
                    tags = {}
                    if 'Tags' in fs:
                        for tag in fs.get('Tags', []):
                            tags[tag.get('Key')] = tag.get('Value')
                    
                    # Determine file system type-specific details
                    fs_type = fs.get('FileSystemType')
                    fs_type_specific = {}
                    
                    if fs_type == 'LUSTRE':
                        fs_type_specific = {
                            'Deployment Type': fs.get('LustreConfiguration', {}).get('DeploymentType', 'N/A'),
                            'Data Repository Configuration': 'Configured' if fs.get('LustreConfiguration', {}).get('DataRepositoryConfiguration') else 'None',
                            'Per Unit Storage Throughput': fs.get('LustreConfiguration', {}).get('PerUnitStorageThroughput', 'N/A'),
                        }
                    elif fs_type == 'WINDOWS':
                        fs_type_specific = {
                            'Throughput Capacity': fs.get('WindowsConfiguration', {}).get('ThroughputCapacity', 'N/A'),
                            'Active Directory ID': fs.get('WindowsConfiguration', {}).get('ActiveDirectoryId', 'N/A'),
                            'Auto Backup': 'Enabled' if fs.get('WindowsConfiguration', {}).get('AutomaticBackupRetentionDays') else 'Disabled',
                        }
                    elif fs_type == 'ONTAP':
                        fs_type_specific = {
                            'Deployment Type': fs.get('OntapConfiguration', {}).get('DeploymentType', 'N/A'),
                            'Endpoint IP Address': fs.get('OntapConfiguration', {}).get('EndpointsIpAddressRange', 'N/A'),
                        }
                    elif fs_type == 'OPENZFS':
                        fs_type_specific = {
                            'Deployment Type': fs.get('OpenZFSConfiguration', {}).get('DeploymentType', 'N/A'),
                            'Throughput Capacity': fs.get('OpenZFSConfiguration', {}).get('ThroughputCapacity', 'N/A'),
                        }
                    
                    # Create resource entry
                    resource_entry = {
                        'Region': self.region,
                        'File System ID': fs.get('FileSystemId', 'N/A'),
                        'File System Type': fs_type,
                        'Storage Capacity': fs.get('StorageCapacity', 'N/A'),
                        'Storage Type': fs.get('StorageType', 'N/A'),
                        'VPC ID': fs.get('VpcId', 'N/A'),
                        'DNS Name': fs.get('DNSName', 'N/A'),
                        'ARN': fs.get('ResourceARN', 'N/A'),
                        'Environment': tags.get('Environment', 'N/A'),
                        'Owner': tags.get('Owner', 'N/A'),
                        'Cost Center': tags.get('CostCenter', 'N/A'),
                    }
                    
                    # Add type-specific details
                    resource_entry.update(fs_type_specific)
                    
                    # Add the resource to results
                    resources.append(resource_entry)
                    
        except Exception as e:
            print(f"Error auditing FSx in region {self.region}: {str(e)}")
            
        return resources