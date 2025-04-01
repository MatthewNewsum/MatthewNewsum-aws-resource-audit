from typing import Dict, List, Any
from .base import AWSService

class Route53Service(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('route53')
        print("Route53Service initialized")  # Debug

    @property
    def service_name(self) -> str:
        return 'route53'

    def audit(self) -> Dict[str, List[Dict[str, Any]]]:
        print("Starting Route53 audit...")  # Debug
        try:
            hosted_zones = self._audit_hosted_zones()
            print(f"Found {len(hosted_zones)} hosted zones")  # Debug
            
            health_checks = self._audit_health_checks()
            print(f"Found {len(health_checks)} health checks")  # Debug
            
            traffic_policies = self._audit_traffic_policies()
            print(f"Found {len(traffic_policies)} traffic policies")  # Debug
            
            results = {
                'hosted_zones': hosted_zones,
                'health_checks': health_checks,
                'traffic_policies': traffic_policies
            }
            print(f"Route53 full results: {results}")  # Debug
            return results
        except Exception as e:
            print(f"Error in Route53 audit: {str(e)}")  # Debug
            return {
                'hosted_zones': [],
                'health_checks': [],
                'traffic_policies': []
            }

    def _audit_hosted_zones(self) -> List[Dict[str, Any]]:
        zones = []
        try:
            paginator = self.client.get_paginator('list_hosted_zones')
            for page in paginator.paginate():
                for zone in page['HostedZones']:
                    zone_details = self._get_zone_details(zone)
                    if zone_details:
                        zones.append(zone_details)
        except Exception as e:
            print(f"Error listing hosted zones: {str(e)}")
        return zones

    def _get_zone_details(self, zone: Dict[str, Any]) -> Dict[str, Any]:
        try:
            records_count = self._count_records(zone['Id'])
            return {
                'Zone Name': zone['Name'],
                'Zone ID': zone['Id'].split('/')[-1],
                'Private Zone': zone['Config']['PrivateZone'],
                'Record Count': records_count,
                'Comment': zone.get('Config', {}).get('Comment', 'N/A'),
                'Resource Record Set Count': zone['ResourceRecordSetCount']
            }
        except Exception as e:
            print(f"Error getting zone details for {zone['Name']}: {str(e)}")
            return None

    def _count_records(self, zone_id: str) -> int:
        try:
            count = 0
            paginator = self.client.get_paginator('list_resource_record_sets')
            for page in paginator.paginate(HostedZoneId=zone_id):
                count += len(page['ResourceRecordSets'])
            return count
        except Exception:
            return 0

    def _audit_health_checks(self) -> List[Dict[str, Any]]:
        checks = []
        try:
            paginator = self.client.get_paginator('list_health_checks')
            for page in paginator.paginate():
                for check in page['HealthChecks']:
                    checks.append({
                        'Health Check ID': check['Id'],
                        'Type': check['HealthCheckConfig'].get('Type', 'N/A'),
                        'Target': check['HealthCheckConfig'].get('IPAddress') or 
                                check['HealthCheckConfig'].get('FullyQualifiedDomainName', 'N/A'),
                        'Port': check['HealthCheckConfig'].get('Port', 'N/A'),
                        'Path': check['HealthCheckConfig'].get('ResourcePath', 'N/A'),
                        'Enabled': not check.get('Disabled', False)
                    })
        except Exception as e:
            print(f"Error listing health checks: {str(e)}")
        return checks

    def _audit_traffic_policies(self) -> List[Dict[str, Any]]:
        policies = []
        try:
            # list_traffic_policies cannot be paginated, so use it directly
            response = self.client.list_traffic_policies(MaxItems='100')
            if 'TrafficPolicies' in response:
                for policy in response['TrafficPolicies']:
                    policies.append({
                        'Policy ID': policy['Id'],
                        'Name': policy['Name'],
                        'Version': policy['LatestVersion'],
                        'Type': policy.get('Type', 'N/A'),
                        'Comment': policy.get('Comment', 'N/A')
                    })
        except Exception as e:
            print(f"Error listing traffic policies: {str(e)}")
        return policies