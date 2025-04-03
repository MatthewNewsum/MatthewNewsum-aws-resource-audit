from typing import Dict, List, Any
from .base import AWSService

class AutoScalingService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('autoscaling', region_name=region)
        self.elb_client = session.client('elbv2', region_name=region)
        
    @property
    def service_name(self) -> str:
        return 'autoscaling'

    def audit(self) -> Dict[str, List[Dict[str, Any]]]:
        try:
            return {
                'auto_scaling_groups': self._audit_auto_scaling_groups(),
                'launch_configurations': self._audit_launch_configurations(),
                'launch_templates': self._audit_launch_templates(),
                'target_groups': self._audit_target_groups(),
                'load_balancers': self._audit_load_balancers()
            }
        except Exception as e:
            print(f"Error auditing AutoScaling in {self.region}: {str(e)}")
            return {
                'auto_scaling_groups': [],
                'launch_configurations': [],
                'launch_templates': [],
                'target_groups': [],
                'load_balancers': []
            }
    
    def _audit_auto_scaling_groups(self) -> List[Dict[str, Any]]:
        groups = []
        try:
            paginator = self.client.get_paginator('describe_auto_scaling_groups')
            for page in paginator.paginate():
                for asg in page['AutoScalingGroups']:
                    tags = {tag['Key']: tag['Value'] for tag in asg.get('Tags', [])}
                    groups.append({
                        'Region': self.region,
                        'Name': asg['AutoScalingGroupName'],
                        'ARN': asg.get('AutoScalingGroupARN', 'N/A'),
                        'Launch Configuration': asg.get('LaunchConfigurationName', 'N/A'),
                        'Launch Template': self._format_launch_template(asg.get('LaunchTemplate', {})),
                        'Min Size': asg['MinSize'],
                        'Max Size': asg['MaxSize'],
                        'Desired Capacity': asg['DesiredCapacity'],
                        'Default Cooldown': asg['DefaultCooldown'],
                        'Health Check Type': asg.get('HealthCheckType', 'N/A'),
                        'Health Check Grace Period': asg.get('HealthCheckGracePeriod', 'N/A'),
                        'Status': self._get_asg_status(asg),
                        'Instance Count': len(asg.get('Instances', [])),
                        'Load Balancers': ', '.join(asg.get('LoadBalancerNames', [])),
                        'Target Groups': ', '.join(asg.get('TargetGroupARNs', [])),
                        'Availability Zones': ', '.join(asg['AvailabilityZones']),
                        'Created Time': str(asg.get('CreatedTime', 'N/A')),
                        'Service Linked Role ARN': asg.get('ServiceLinkedRoleARN', 'N/A'),
                        'Name Tag': tags.get('Name', 'N/A'),
                        'VPC Zone Identifier': asg.get('VPCZoneIdentifier', 'N/A')
                    })
            
        except Exception as e:
            print(f"Error listing Auto Scaling groups: {str(e)}")
        
        return groups
        
    def _audit_launch_configurations(self) -> List[Dict[str, Any]]:
        configs = []
        try:
            paginator = self.client.get_paginator('describe_launch_configurations')
            for page in paginator.paginate():
                for config in page['LaunchConfigurations']:
                    configs.append({
                        'Region': self.region,
                        'Name': config['LaunchConfigurationName'],
                        'ARN': config.get('LaunchConfigurationARN', 'N/A'),
                        'Image ID': config.get('ImageId', 'N/A'),
                        'Instance Type': config.get('InstanceType', 'N/A'),
                        'Key Name': config.get('KeyName', 'N/A'),
                        'Security Groups': ', '.join(config.get('SecurityGroups', [])),
                        'User Data': 'Present' if config.get('UserData') else 'None',
                        'IAM Instance Profile': config.get('IamInstanceProfile', 'N/A'),
                        'Created Time': str(config.get('CreatedTime', 'N/A')),
                        'EBS Optimized': config.get('EbsOptimized', False),
                        'Instance Monitoring': config.get('InstanceMonitoring', {}).get('Enabled', False)
                    })
            
        except Exception as e:
            print(f"Error listing launch configurations: {str(e)}")
        
        return configs
    
    def _audit_launch_templates(self) -> List[Dict[str, Any]]:
        templates = []
        try:
            ec2_client = self.session.client('ec2', region_name=self.region)
            paginator = ec2_client.get_paginator('describe_launch_templates')
            for page in paginator.paginate():
                for template in page['LaunchTemplates']:
                    templates.append({
                        'Region': self.region,
                        'ID': template['LaunchTemplateId'],
                        'Name': template['LaunchTemplateName'],
                        'Version': template['LatestVersionNumber'],
                        'Default Version': template['DefaultVersionNumber'],
                        'Created By': template.get('CreatedBy', 'N/A'),
                        'Created Time': str(template.get('CreateTime', 'N/A'))
                    })
            
        except Exception as e:
            print(f"Error listing launch templates: {str(e)}")
        
        return templates
    
    def _audit_target_groups(self) -> List[Dict[str, Any]]:
        target_groups = []
        try:
            paginator = self.elb_client.get_paginator('describe_target_groups')
            for page in paginator.paginate():
                for tg in page['TargetGroups']:
                    # Get targets health
                    try:
                        health_response = self.elb_client.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
                        # Check if health_response is a string before trying to access it as a dict
                        if isinstance(health_response, dict) and 'TargetHealthDescriptions' in health_response:
                            health_descriptions = health_response['TargetHealthDescriptions']
                            healthy_count = len([t for t in health_descriptions 
                                               if t.get('TargetHealth', {}).get('State') == 'healthy'])
                            unhealthy_count = len([t for t in health_descriptions 
                                                 if t.get('TargetHealth', {}).get('State', '') != 'healthy'])
                            total_count = len(health_descriptions)
                        else:
                            healthy_count = unhealthy_count = total_count = 0
                            print(f"Warning: Unexpected target health response format for {tg['TargetGroupArn']}")
                    except Exception as health_error:
                        print(f"Error getting target health: {str(health_error)}")
                        healthy_count = unhealthy_count = total_count = 0
                    
                    # Create a dictionary with safe data access using .get() method
                    target_groups.append({
                        'Region': self.region,
                        'Target Group Name': tg.get('TargetGroupName', 'N/A'),
                        'ARN': tg.get('TargetGroupArn', 'N/A'),
                        'Protocol': tg.get('Protocol', 'N/A'),
                        'Port': tg.get('Port', 'N/A'),
                        'VPC ID': tg.get('VpcId', 'N/A'),
                        'Target Type': tg.get('TargetType', 'instance'),
                        'Health Check Protocol': tg.get('HealthCheckProtocol', 'N/A'),
                        'Health Check Port': tg.get('HealthCheckPort', 'N/A'),
                        'Health Check Path': tg.get('HealthCheckPath', 'N/A'),
                        'Healthy Threshold': tg.get('HealthyThresholdCount', 'N/A'),
                        'Unhealthy Threshold': tg.get('UnhealthyThresholdCount', 'N/A'),
                        'Timeout': tg.get('HealthCheckTimeoutSeconds', 'N/A'),
                        'Interval': tg.get('HealthCheckIntervalSeconds', 'N/A'),
                        'Total Targets': total_count,
                        'Healthy Targets': healthy_count,
                        'Unhealthy Targets': unhealthy_count,
                        'Load Balancer ARNs': ', '.join([lb.get('LoadBalancerArn', '') 
                                                      for lb in tg.get('LoadBalancerArns', []) 
                                                      if isinstance(lb, dict)])
                    })
            
        except Exception as e:
            print(f"Error listing target groups: {str(e)}")
            # Print more detailed error information for debugging
            import traceback
            print(traceback.format_exc())
        
        return target_groups
    
    def _audit_load_balancers(self) -> List[Dict[str, Any]]:
        load_balancers = []
        try:
            paginator = self.elb_client.get_paginator('describe_load_balancers')
            for page in paginator.paginate():
                for lb in page['LoadBalancers']:
                    # Get tags
                    try:
                        tags_response = self.elb_client.describe_tags(
                            ResourceArns=[lb['LoadBalancerArn']]
                        )
                        tag_desc = tags_response.get('TagDescriptions', [{}])[0]
                        tags = {tag['Key']: tag['Value'] for tag in tag_desc.get('Tags', [])}
                    except:
                        tags = {}
                    
                    load_balancers.append({
                        'Region': self.region,
                        'Load Balancer Name': lb['LoadBalancerName'],
                        'ARN': lb['LoadBalancerArn'],
                        'Type': lb['Type'],
                        'Scheme': lb.get('Scheme', 'N/A'),
                        'VPC ID': lb.get('VpcId', 'N/A'),
                        'State': lb.get('State', {}).get('Code', 'N/A'),
                        'DNS Name': lb.get('DNSName', 'N/A'),
                        'Created Time': str(lb.get('CreatedTime', 'N/A')),
                        'Availability Zones': ', '.join([az['ZoneName'] for az in lb.get('AvailabilityZones', [])]),
                        'Security Groups': ', '.join(lb.get('SecurityGroups', [])),
                        'IP Address Type': lb.get('IpAddressType', 'N/A'),
                        'Name Tag': tags.get('Name', 'N/A')
                    })
            
        except Exception as e:
            print(f"Error listing load balancers: {str(e)}")
        
        return load_balancers
    
    def _get_asg_status(self, asg: Dict[str, Any]) -> str:
        """Determine the status of an Auto Scaling Group based on its properties"""
        if asg.get('Status'):
            return asg['Status']
            
        if len(asg.get('SuspendedProcesses', [])) > 0:
            return 'Suspended'
            
        return 'Active'
    
    def _format_launch_template(self, launch_template: Dict[str, Any]) -> str:
        """Format launch template info into a readable string"""
        if not launch_template:
            return 'N/A'
            
        template_id = launch_template.get('LaunchTemplateId', '')
        template_name = launch_template.get('LaunchTemplateName', '')
        version = launch_template.get('Version', '')
            
        if template_name and version:
            return f"{template_name} (v{version})"
        elif template_name:
            return template_name
        elif template_id:
            return f"ID: {template_id}"
        else:
            return 'N/A'