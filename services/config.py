from typing import Dict, List, Any
from .base import AWSService
from botocore.exceptions import ClientError

class ConfigService(AWSService):
    """Service class for AWS Config"""

    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('config', region_name=region)
        
    @property
    def service_name(self) -> str:
        return 'config'

    def audit(self) -> Dict[str, List[Dict[str, Any]]]:
        try:
            return {
                'recorders': self._audit_recorders(),
                'rules': self._audit_rules(),
                'conformance_packs': self._audit_conformance_packs(),
                'aggregators': self._audit_aggregators()
            }
        except Exception as e:
            print(f"Error auditing Config in {self.region}: {str(e)}")
            return {
                'recorders': [],
                'rules': [],
                'conformance_packs': [],
                'aggregators': []
            }
            
    def _audit_recorders(self) -> List[Dict[str, Any]]:
        recorders = []
        try:
            response = self.client.describe_configuration_recorders()
            for recorder in response.get('ConfigurationRecorders', []):
                # Get recorder status
                status = {}
                try:
                    status_response = self.client.describe_configuration_recorder_status(
                        ConfigurationRecorderNames=[recorder['name']]
                    )
                    if status_response.get('ConfigurationRecordersStatus'):
                        status = status_response['ConfigurationRecordersStatus'][0]
                except Exception as e:
                    print(f"Error getting recorder status for {recorder['name']}: {str(e)}")
                
                recorders.append({
                    'Region': self.region,
                    'Name': recorder['name'],
                    'Role ARN': recorder['roleARN'],
                    'Recording All Resource Types': recorder['recordingGroup'].get('allSupported', False),
                    'Recording': status.get('recording', False),
                    'Last Status': status.get('lastStatus', 'N/A'),
                    'Last Start Time': str(status.get('lastStartTime', 'N/A')),
                    'Last Stop Time': str(status.get('lastStopTime', 'N/A')),
                    'Last Error Code': status.get('lastErrorCode', 'N/A'),
                    'Last Error Message': status.get('lastErrorMessage', 'N/A')
                })
        except Exception as e:
            print(f"Error listing Config recorders: {str(e)}")
        return recorders
    
    def _audit_rules(self) -> List[Dict[str, Any]]:
        rules = []
        try:
            paginator = self.client.get_paginator('describe_config_rules')
            for page in paginator.paginate():
                for rule in page.get('ConfigRules', []):
                    # Get compliance status
                    compliance = 'UNKNOWN'
                    try:
                        compliance_response = self.client.describe_compliance_by_config_rule(
                            ConfigRuleNames=[rule['ConfigRuleName']]
                        )
                        if compliance_response.get('ComplianceByConfigRules'):
                            compliance = compliance_response['ComplianceByConfigRules'][0].get('Compliance', {}).get('ComplianceType', 'UNKNOWN')
                    except Exception:
                        pass
                    
                    rule_source = rule.get('Source', {})
                    
                    rules.append({
                        'Region': self.region,
                        'Rule Name': rule['ConfigRuleName'],
                        'Rule ID': rule['ConfigRuleId'],
                        'Description': rule.get('Description', 'N/A'),
                        'Source Type': rule_source.get('SourceIdentifier', 'N/A'),
                        'Source Owner': rule_source.get('Owner', 'N/A'),
                        'Scope': self._format_scope(rule.get('Scope', {})),
                        'Compliance': compliance,
                        'Created By': rule.get('CreatedBy', 'N/A'),
                        'Last Modified': str(rule.get('LastModifiedTime', 'N/A'))
                    })
        except Exception as e:
            print(f"Error listing Config rules: {str(e)}")
        return rules
    
    def _audit_conformance_packs(self) -> List[Dict[str, Any]]:
        packs = []
        try:
            paginator = self.client.get_paginator('describe_conformance_packs')
            for page in paginator.paginate():
                for pack in page.get('ConformancePackDetails', []):
                    packs.append({
                        'Region': self.region,
                        'Name': pack['ConformancePackName'],
                        'ARN': pack['ConformancePackArn'],
                        'Delivery S3 Bucket': pack.get('DeliveryS3Bucket', 'N/A'),
                        'Delivery S3 Key Prefix': pack.get('DeliveryS3KeyPrefix', 'N/A'),
                        'Last Update Requested': str(pack.get('LastUpdateRequestedTime', 'N/A')),
                        'Created By': pack.get('CreatedBy', 'N/A')
                    })
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchConformancePackException':
                print(f"Error listing conformance packs: {str(e)}")
        except Exception as e:
            print(f"Error listing conformance packs: {str(e)}")
        return packs
    
    def _audit_aggregators(self) -> List[Dict[str, Any]]:
        aggregators = []
        try:
            response = self.client.describe_configuration_aggregators()
            for agg in response.get('ConfigurationAggregators', []):
                account_aggregation_sources = agg.get('AccountAggregationSources', [])
                org_aggregation_source = agg.get('OrganizationAggregationSource', {})
                
                source_accounts = []
                if account_aggregation_sources:
                    source_accounts = [src.get('AccountIds', []) for src in account_aggregation_sources]
                    # Flatten list of lists
                    source_accounts = [acc for sublist in source_accounts for acc in sublist]
                
                aggregators.append({
                    'Region': self.region,
                    'Name': agg['ConfigurationAggregatorName'],
                    'ARN': agg['ConfigurationAggregatorArn'],
                    'Source Type': 'Organization' if org_aggregation_source else 'Account',
                    'Source Accounts': ', '.join(source_accounts) if source_accounts else 'N/A',
                    'Organization Source Role': org_aggregation_source.get('RoleArn', 'N/A') if org_aggregation_source else 'N/A',
                    'Created By': agg.get('CreatedBy', 'N/A'),
                    'Creation Time': str(agg.get('CreationTime', 'N/A')),
                    'Last Updated Time': str(agg.get('LastUpdatedTime', 'N/A'))
                })
        except Exception as e:
            print(f"Error listing configuration aggregators: {str(e)}")
        return aggregators
    
    def _format_scope(self, scope: Dict) -> str:
        """Format the scope of a Config rule"""
        if not scope:
            return 'All resources'
        
        if scope.get('ComplianceResourceTypes'):
            return f"Resource types: {', '.join(scope['ComplianceResourceTypes'])}"
        elif scope.get('ComplianceResourceId'):
            return f"Resource ID: {scope['ComplianceResourceId']}"
        else:
            return 'Custom scope'