from typing import Dict, List, Any
from .base import AWSService

class VPCService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('ec2', region_name=region)  # VPC uses EC2 client
        
    @property
    def service_name(self) -> str:
        return 'vpc'

    def audit(self) -> List[Dict[str, Any]]:
        vpc_details = []
        try:
            response = self.client.describe_vpcs()
            for vpc in response.get('Vpcs', []):
                details = self._get_vpc_details(vpc)
                if details:
                    vpc_details.append(details)
        except Exception as e:
            print(f"Error listing VPCs: {str(e)}")
        return vpc_details

    def _get_vpc_details(self, vpc: Dict) -> Dict[str, Any]:
        vpc_id = vpc['VpcId']
        try:
            base_details = self._get_base_vpc_info(vpc)
            additional_details = {
                'subnets': self._get_subnets(vpc_id),
                'route_tables': self._get_route_tables(vpc_id),
                'security_groups': self._get_security_groups(vpc_id),
                'vpc_endpoints': self._get_vpc_endpoints(vpc_id),
                'peering_connections': self._get_vpc_peering(vpc_id),
                'transit_gateway': self._get_transit_gateway_details(vpc_id)
            }
            
            base_details.update(additional_details)
            base_details.update(self._get_resource_counts(additional_details))
            
            return base_details
            
        except Exception as e:
            print(f"Error processing VPC {vpc_id}: {str(e)}")
            return None

    def _get_base_vpc_info(self, vpc: Dict) -> Dict[str, Any]:
        tags = {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])}
        flow_logs = self.client.describe_flow_logs(
            Filters=[{'Name': 'resource-id', 'Values': [vpc['VpcId']]}]
        )['FlowLogs']
        
        return {
            'Region': self.region,
            'VPC ID': vpc['VpcId'],
            'Name': tags.get('Name', 'N/A'),
            'CIDR Block': vpc['CidrBlock'],
            'State': vpc['State'],
            'Is Default': vpc.get('IsDefault', False),
            'DNS Hostnames Enabled': vpc.get('EnableDnsHostnames', False),
            'DNS Support Enabled': vpc.get('EnableDnsSupport', True),
            'Flow Logs Enabled': len(flow_logs) > 0
        }

    def _get_route_tables(self, vpc_id: str) -> List[Dict[str, Any]]:
        route_tables = []
        paginator = self.client.get_paginator('describe_route_tables')
        
        for page in paginator.paginate(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]):
            for rt in page['RouteTables']:
                route_tables.append(self._format_route_table(rt))
                
        return route_tables

    def _get_security_groups(self, vpc_id: str) -> List[Dict[str, Any]]:
        security_groups = []
        paginator = self.client.get_paginator('describe_security_groups')
        
        for page in paginator.paginate(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]):
            for sg in page['SecurityGroups']:
                security_groups.append(self._format_security_group(sg))
                
        return security_groups

    def _format_route_table(self, rt: Dict) -> Dict[str, Any]:
        routes = []
        for route in rt.get('Routes', []):
            route_entry = {
                'Destination': route.get('DestinationCidrBlock', route.get('DestinationPrefixListId', 'N/A')),
                'Target': next((v for k, v in route.items() if k.endswith('Id') and v), 'N/A'),
                'State': route.get('State', 'N/A'),
                'Type': next((k.replace('Gateway', '').replace('Id', '') for k in route.keys() if k.endswith('Id')), 'N/A')
            }
            routes.append(route_entry)

        return {
            'Region': self.region,
            'VPC ID': rt.get('VpcId', 'N/A'),
            'Route Table ID': rt['RouteTableId'],
            'Name': next((tag['Value'] for tag in rt.get('Tags', []) 
                        if tag['Key'] == 'Name'), 'N/A'),
            'Main': any(assoc.get('Main', False) for assoc in rt.get('Associations', [])),
            'Associated Subnets': ', '.join([assoc['SubnetId'] for assoc in rt.get('Associations', []) 
                                        if 'SubnetId' in assoc]),
            'Routes': routes
        }

    def _format_security_group(self, sg: Dict) -> Dict[str, Any]:
        return {
            'Region': self.region,
            'VPC ID': sg.get('VpcId', 'N/A'),
            'Security Group ID': sg['GroupId'],
            'Name': sg['GroupName'],
            'Description': sg['Description']
        }

    def _get_vpc_endpoints(self, vpc_id: str) -> List[Dict[str, Any]]:
        try:
            endpoints = self.client.describe_vpc_endpoints(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )['VpcEndpoints']
            return endpoints
        except Exception:
            return []

    def _get_vpc_peering(self, vpc_id: str) -> List[Dict[str, Any]]:
        try:
            peering = self.client.describe_vpc_peering_connections(
                Filters=[{'Name': 'requester-vpc-info.vpc-id', 'Values': [vpc_id]}]
            )['VpcPeeringConnections']
            return peering
        except Exception:
            return []

    def _get_transit_gateway_details(self, vpc_id: str) -> Dict[str, Any]:
        try:
            # Get TGW attachments for this VPC
            attachments = self.client.describe_transit_gateway_attachments(
                Filters=[
                    {'Name': 'resource-id', 'Values': [vpc_id]},
                    {'Name': 'resource-type', 'Values': ['vpc']}
                ]
            )['TransitGatewayAttachments']

            # Get TGW route tables associated with these attachments
            route_tables = []
            for attachment in attachments:
                try:
                    tgw_id = attachment['TransitGatewayId']
                    response = self.client.describe_transit_gateway_route_tables(
                        Filters=[{'Name': 'transit-gateway-id', 'Values': [tgw_id]}]
                    )
                    route_tables.extend(response['TransitGatewayRouteTables'])
                except Exception as e:
                    print(f"Error getting TGW route tables for {tgw_id}: {str(e)}")

            return {
                'attachments': [{
                    'TransitGatewayId': att['TransitGatewayId'],
                    'State': att['State'],
                    'AssociationState': att.get('Association', {}).get('State', 'N/A'),
                    'CreationTime': str(att['CreationTime'])
                } for att in attachments],
                'route_tables': [{
                    'TransitGatewayRouteTableId': rt['TransitGatewayRouteTableId'],
                    'State': rt['State'],
                    'CreationTime': str(rt['CreationTime'])
                } for rt in route_tables]
            }
        except Exception as e:
            print(f"Error getting transit gateway details for VPC {vpc_id}: {str(e)}")
            return {'attachments': [], 'route_tables': []}

    def _get_subnets(self, vpc_id: str) -> List[Dict[str, Any]]:
        subnets = []
        try:
            paginator = self.client.get_paginator('describe_subnets')
            for page in paginator.paginate(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]):
                for subnet in page['Subnets']:
                    tags = {tag['Key']: tag['Value'] for tag in subnet.get('Tags', [])}
                    subnets.append({
                        'Region': self.region,
                        'VPC ID': vpc_id,
                        'Subnet ID': subnet['SubnetId'],
                        'Name': tags.get('Name', 'N/A'),
                        'CIDR Block': subnet['CidrBlock'],
                        'Availability Zone': subnet['AvailabilityZone'],
                        'State': subnet['State'],
                        'Available IPs': subnet['AvailableIpAddressCount'],
                        'Auto-assign Public IP': subnet.get('MapPublicIpOnLaunch', False),
                        'Default for AZ': subnet.get('DefaultForAz', False)
                    })
        except Exception as e:
            print(f"Error getting subnets for VPC {vpc_id}: {str(e)}")
        return subnets

    def _get_resource_counts(self, details: Dict[str, List]) -> Dict[str, int]:
        return {
            'Subnet Count': len(details['subnets']),
            'Route Tables': len(details['route_tables']),
            'Security Groups': len(details['security_groups']),
            'VPC Endpoints': len(details['vpc_endpoints']),
            'Peering Connections': len(details['peering_connections']),
            'Transit Gateway Attachments': len(details['transit_gateway'].get('attachments', [])),
            'Transit Gateway Route Tables': len(details['transit_gateway'].get('route_tables', []))
        }