import os
import json
import pandas as pd
from datetime import datetime
import traceback
from typing import Any, Dict, List, Optional, Union

class ReportGenerationError(Exception):
    """Exception raised when report generation fails."""
    pass

class ReportGenerator:
    def __init__(self, results: Dict, output_dir: str = 'results'):
        """Initialize the ReportGenerator with audit results and output directory."""
        self.results = results
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_reports(self):
        """Generate JSON and Excel reports from audit results."""
        try:
            print("\nGenerating reports...\n")
            
            # Generate JSON report
            json_path = self._save_json_report()
            print(f"JSON report saved to: {json_path}\n")
            
            # Generate Excel report
            try:
                print("Generating Excel report...")
                excel_path = self._generate_excel_report()
                print(f"Excel report saved to: {excel_path}")
                return json_path, excel_path
            except Exception as e:
                print(f"Error generating Excel report: {str(e)}")
                print(traceback.format_exc())
                # Return just the JSON path if Excel generation fails
                return json_path, None
            
        except Exception as e:
            print(f"Error generating reports: {str(e)}")
            print(traceback.format_exc())
            raise ReportGenerationError(f"Failed to generate reports: {str(e)}")
    
    def _save_json_report(self) -> str:
        """Save audit results as JSON file."""
        json_path = os.path.join(self.output_dir, f'aws_inventory_{self.timestamp}.json')
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        return json_path

    def _generate_excel_report(self) -> str:
        """Generate Excel report with multiple sheets for different resource types."""
        excel_path = os.path.join(self.output_dir, f'aws_inventory_{self.timestamp}.xlsx')
        
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            workbook = writer.book
            header_format = self._get_header_format(workbook)
            
            self._write_global_resources(writer, header_format)
            self._write_regional_resources(writer, header_format)
            self._write_resource_usage_by_region(writer, header_format)
            self._write_summary(writer, header_format)

        return excel_path
    
    def _get_header_format(self, workbook) -> Any:
        """Create and return a format for Excel headers."""
        return workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
    
    def _write_dataframe(self, writer: pd.ExcelWriter, sheet_name: str, data: List[Dict], header_format: Any) -> None:
        """Write a list of dictionaries to a sheet as a pandas DataFrame."""
        # Handle empty data case
        if not data:
            df = pd.DataFrame([{"No Data": "No resources found"}])
        else:
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Format the header
        worksheet = writer.sheets[sheet_name]
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Adjust column width (optional)
        for col_num, column in enumerate(df.columns):
            max_width = max(
                df[column].astype(str).map(len).max(),  # Width of largest data
                len(column)  # Width of column header
            ) + 2  
            worksheet.set_column(col_num, col_num, max_width)
        
        print(f"  Added {len(df)} rows to {sheet_name}")

    def _write_global_resources(self, writer: pd.ExcelWriter, header_format: Any) -> None:
        """Write global (non-regional) resources to Excel sheets."""
        print("Writing global resources...")
        
        try:
            if 'global_services' not in self.results:
                print("No global services data available")
                return
            
            # Add IAM data handling here
            if 'iam' in self.results['global_services']:
                print("Processing IAM data...")
                iam_data = self.results['global_services']['iam']
                
                # Process IAM users
                if iam_data.get('users'):
                    self._write_dataframe(
                        writer,
                        'IAM Users',
                        iam_data['users'],
                        header_format
                    )
                
                # Process IAM roles
                if iam_data.get('roles'):
                    self._write_dataframe(
                        writer,
                        'IAM Roles',
                        iam_data['roles'],
                        header_format
                    )
                
                # Process IAM groups
                if iam_data.get('groups'):
                    self._write_dataframe(
                        writer,
                        'IAM Groups',
                        iam_data['groups'],
                        header_format
                    )
            
            print(f"Available global services: {self.results['global_services'].keys()}")
            
            # Handle Route53 resources
            if 'route53' in self.results['global_services']:
                print("Processing Route53 data...")
                route53_data = self.results['global_services']['route53']
                print(f"Route53 data keys: {route53_data.keys()}")
                
                # Process hosted zones
                if route53_data.get('hosted_zones'):
                    hosted_zones = route53_data['hosted_zones']
                    if isinstance(hosted_zones, list) and hosted_zones:
                        print(f"Writing {len(hosted_zones)} hosted zones")
                        self._write_dataframe(
                            writer,
                            'Route53 Hosted Zones',
                            hosted_zones,
                            header_format
                        )
                    else:
                        print(f"No hosted zones to write or invalid data type: {type(hosted_zones)}")
                
                # Process health checks - ensure it's a list
                if route53_data.get('health_checks'):
                    health_checks = route53_data['health_checks']
                    if isinstance(health_checks, str):
                        print(f"WARNING: health_checks is a string: '{health_checks}', converting to empty list")
                        health_checks = []
                    
                    if health_checks:  # Only write if there are items
                        print(f"Writing {len(health_checks)} health checks")
                        self._write_dataframe(
                            writer,
                            'Route53 Health Checks',
                            health_checks,
                            header_format
                        )
                    else:
                        print("No health checks to write")
                
                # Process traffic policies - ensure it's a list
                if route53_data.get('traffic_policies'):
                    traffic_policies = route53_data['traffic_policies']
                    if isinstance(traffic_policies, str):
                        print(f"WARNING: traffic_policies is a string: '{traffic_policies}', converting to empty list")
                        traffic_policies = []
                    
                    if traffic_policies:  # Only write if there are items
                        print(f"Writing {len(traffic_policies)} traffic policies")
                        self._write_dataframe(
                            writer,
                            'Route53 Traffic Policies',
                            traffic_policies,
                            header_format
                        )
                    else:
                        print("No traffic policies to write")
                
                # Process zone records - ensure it's a list
                if route53_data.get('zone_records'):
                    zone_records = route53_data['zone_records']
                    if isinstance(zone_records, str):
                        print(f"WARNING: zone_records is a string: '{zone_records}', converting to empty list")
                        zone_records = []
                    
                    if zone_records:  # Only write if there are items
                        print(f"Writing {len(zone_records)} zone records")
                        self._write_dataframe(
                            writer,
                            'Route53 Zone Records',
                            zone_records,
                            header_format
                        )
                    else:
                        print("No zone records to write")
                        
            # Handle other global services here (IAM, etc.)
            
        except Exception as e:
            print(f"Error writing global resources: {str(e)}")
            print(traceback.format_exc())
            # Continue with the rest of the report rather than failing

    def _write_regional_resources(self, writer: pd.ExcelWriter, header_format: Any) -> None:
        """Write regional resources to Excel sheets."""
        print("Writing regional resources...")
        
        # Process autoscaling resources
        auto_scaling_groups = []
        launch_configurations = []
        launch_templates = []
        target_groups = []
        load_balancers = []
        
        # Extract autoscaling data from all regions
        for region, services in self.results['regions'].items():
            if 'autoscaling' in services and isinstance(services['autoscaling'], dict):
                autoscaling_data = services['autoscaling']
                
                # Process auto scaling groups
                if 'auto_scaling_groups' in autoscaling_data:
                    for asg in autoscaling_data['auto_scaling_groups']:
                        auto_scaling_groups.append(asg)
                
                # Process launch configurations
                if 'launch_configurations' in autoscaling_data:
                    for lc in autoscaling_data['launch_configurations']:
                        launch_configurations.append(lc)
                
                # Process launch templates
                if 'launch_templates' in autoscaling_data:
                    for lt in autoscaling_data['launch_templates']:
                        launch_templates.append(lt)
                
                # Process target groups
                if 'target_groups' in autoscaling_data:
                    for tg in autoscaling_data['target_groups']:
                        target_groups.append(tg)
                
                # Process load balancers
                if 'load_balancers' in autoscaling_data:
                    for lb in autoscaling_data['load_balancers']:
                        load_balancers.append(lb)
        
        # Write autoscaling data if available
        if auto_scaling_groups:
            self._write_dataframe(writer, 'Auto Scaling Groups', auto_scaling_groups, header_format)
        
        if launch_configurations:
            self._write_dataframe(writer, 'Launch Configurations', launch_configurations, header_format)
        
        if launch_templates:
            self._write_dataframe(writer, 'Launch Templates', launch_templates, header_format)
        
        if target_groups:
            self._write_dataframe(writer, 'Target Groups', target_groups, header_format)
        
        if load_balancers:
            self._write_dataframe(writer, 'Load Balancers', load_balancers, header_format)
        
        # Existing resource processing code...
        if 'regions' not in self.results:
            return

        # Create a sheet for each resource type across all regions
        resource_types_map = {
            'ec2': 'EC2 Instances',
            'rds': 'RDS Instances',
            'lambda': 'Lambda Functions',
            'dynamodb': 'DynamoDB Tables',
            'bedrock': 'Bedrock Models',
            's3': 'S3 Buckets',
            'fsx': 'FSx',
            'sns': 'SNS Topics',
            'dms': 'DMS Resources',
            # Add other resource types as needed
        }

        # For each resource type, collect data from all regions
        for resource_type, sheet_name in resource_types_map.items():
            all_resources = []
            
            # Collect resources of this type from all regions
            for region, services in self.results['regions'].items():
                if resource_type in services:
                    if isinstance(services[resource_type], list):
                        for resource in services[resource_type]:
                            if isinstance(resource, dict):  # Make sure it's a dict before modifying
                                # Ensure 'Region' is included if not already
                                if 'Region' not in resource:
                                    resource['Region'] = region
                                all_resources.append(resource)
                            else:
                                # Handle non-dictionary resources
                                print(f"Warning: Resource in {resource_type} is not a dictionary: {type(resource)}")
                                # Create a simple dict with the string value
                                if isinstance(resource, str):
                                    all_resources.append({'Value': resource, 'Region': region})
                    elif isinstance(services[resource_type], dict) and 'error' in services[resource_type]:
                        # Handle error case
                        error_msg = services[resource_type]['error']
                        all_resources.append({'Region': region, 'Error': error_msg})
                    
            # Write the collected resources to a sheet
            if all_resources:
                self._write_dataframe(writer, sheet_name, all_resources, header_format)
        
        # Add this section for Config resources
        config_recorders = []
        config_rules = []
        config_conformance_packs = []
        config_aggregators = []
        
        for region, data in self.results['regions'].items():
            if 'config' in data and isinstance(data['config'], dict):
                config_data = data['config']
                for recorder in config_data.get('recorders', []):
                    recorder['Region'] = region
                    config_recorders.append(recorder)
                for rule in config_data.get('rules', []):
                    rule['Region'] = region
                    config_rules.append(rule)
                for pack in config_data.get('conformance_packs', []):
                    pack['Region'] = region
                    config_conformance_packs.append(pack)
                for agg in config_data.get('aggregators', []):
                    agg['Region'] = region
                    config_aggregators.append(agg)
        
        # Write Config recorders
        if config_recorders:
            df_recorders = pd.DataFrame(config_recorders)
            df_recorders.to_excel(writer, sheet_name='Config Recorders', index=False)
            self._format_sheet(writer.sheets['Config Recorders'], df_recorders, header_format)
        
        # Write Config rules
        if config_rules:
            df_rules = pd.DataFrame(config_rules)
            df_rules.to_excel(writer, sheet_name='Config Rules', index=False)
            self._format_sheet(writer.sheets['Config Rules'], df_rules, header_format)
        
        # Write Conformance packs
        if config_conformance_packs:
            df_packs = pd.DataFrame(config_conformance_packs)
            df_packs.to_excel(writer, sheet_name='Config Conformance Packs', index=False)
            self._format_sheet(writer.sheets['Config Conformance Packs'], df_packs, header_format)
        
        # Write Config aggregators
        if config_aggregators:
            df_aggregators = pd.DataFrame(config_aggregators)
            df_aggregators.to_excel(writer, sheet_name='Config Aggregators', index=False)
            self._format_sheet(writer.sheets['Config Aggregators'], df_aggregators, header_format)

        # Add VPC resources
        vpc_resources = []
        vpc_subnets = []
        vpc_security_groups = []
        
        # Process VPC data from all regions
        for region, services in self.results['regions'].items():
            if 'vpc' in services and isinstance(services['vpc'], list):
                for vpc in services['vpc']:
                    # Add region if not present
                    if isinstance(vpc, dict):
                        vpc['Region'] = region
                        vpc_resources.append(vpc)
                        
                        # Process subnets if they exist
                        if 'subnets' in vpc and isinstance(vpc['subnets'], list):
                            for subnet in vpc['subnets']:
                                subnet['Region'] = region
                                subnet['VPC ID'] = vpc.get('VPC ID', '')
                                vpc_subnets.append(subnet)
                        
                        # Process security groups
                        if 'security_groups' in vpc and isinstance(vpc['security_groups'], list):
                            for sg in vpc['security_groups']:
                                sg['Region'] = region
                                sg['VPC ID'] = vpc.get('VPC ID', '')
                                vpc_security_groups.append(sg)
        
        # Write VPC resources if available
        if vpc_resources:
            self._write_dataframe(writer, 'VPCs', vpc_resources, header_format)
        
        if vpc_subnets:
            self._write_dataframe(writer, 'VPC Subnets', vpc_subnets, header_format)
        
        if vpc_security_groups:
            self._write_dataframe(writer, 'Security Groups', vpc_security_groups, header_format)

        # Add DMS resources
        dms_replication_instances = []
        dms_replication_tasks = []
        dms_endpoints = []
        dms_subnet_groups = []
        
        # Process DMS data from all regions
        for region, services in self.results['regions'].items():
            if 'dms' in services and isinstance(services['dms'], dict):
                dms_data = services['dms']
                
                # Process replication instances
                if 'replication_instances' in dms_data:
                    for instance in dms_data['replication_instances']:
                        instance['Region'] = region
                        dms_replication_instances.append(instance)
                
                # Process replication tasks
                if 'replication_tasks' in dms_data:
                    for task in dms_data['replication_tasks']:
                        task['Region'] = region
                        dms_replication_tasks.append(task)
                
                # Process endpoints
                if 'endpoints' in dms_data:
                    for endpoint in dms_data['endpoints']:
                        endpoint['Region'] = region
                        dms_endpoints.append(endpoint)
                
                # Process subnet groups
                if 'replication_subnet_groups' in dms_data:
                    for subnet_group in dms_data['replication_subnet_groups']:
                        subnet_group['Region'] = region
                        dms_subnet_groups.append(subnet_group)
        
        # Write DMS resources if available
        if dms_replication_instances:
            self._write_dataframe(writer, 'DMS Replication Instances', dms_replication_instances, header_format)
        
        if dms_replication_tasks:
            self._write_dataframe(writer, 'DMS Replication Tasks', dms_replication_tasks, header_format)
        
        if dms_endpoints:
            self._write_dataframe(writer, 'DMS Endpoints', dms_endpoints, header_format)
        
        if dms_subnet_groups:
            self._write_dataframe(writer, 'DMS Subnet Groups', dms_subnet_groups, header_format)

    def _write_resource_usage_by_region(self, writer, header_format):
        """Write resource usage by region."""
        print("Writing resource usage by region...")
        
        # Initialize the data structure
        region_rows = []
        # Initialize total_by_type dictionary here
        total_by_type = {}
    
        resource_types = [
            ('EC2 Instances', 'ec2'),
            ('RDS Instances', 'rds'),
            ('S3 Buckets', 's3'),
            ('Lambda Functions', 'lambda'),
            ('DynamoDB Tables', 'dynamodb'),
            ('VPCs', 'vpc'),
            ('Auto Scaling Groups', 'autoscaling.auto_scaling_groups'),
            ('Launch Configurations', 'autoscaling.launch_configurations'),
            ('Launch Templates', 'autoscaling.launch_templates'),
            ('Target Groups', 'autoscaling.target_groups'),
            ('Load Balancers', 'autoscaling.load_balancers'),
            ('Config Recorders', 'config.recorders'),
            ('Config Rules', 'config.rules'),
            ('Config Conformance Packs', 'config.conformance_packs'),
            ('Config Aggregators', 'config.aggregators'),
            ('Athena Workgroups', 'athena.workgroups'),
            ('Bedrock Models', 'bedrock'),
            ('FSx File Systems', 'fsx'),
            ('IAM Users', 'global_services.iam.users'),
            ('IAM Roles', 'global_services.iam.roles'),
            ('IAM Groups', 'global_services.iam.groups'),
            ('SNS Topics', 'sns'),
            ('SNS Subscriptions', 'sns.subscriptions')
        ]
        
        # Initialize the total_by_type counters for all resource types
        for resource_name, _ in resource_types:
            total_by_type[resource_name] = 0
            
        # Calculate counts by region
        for region, data in self.results['regions'].items():
            region_total = 0
            row = {'Region': region}
            
            for resource_name, resource_path in resource_types:
                count = 0
                
                if '.' in resource_path:  # For nested resources like config.recorders
                    path_parts = resource_path.split('.')
                    if len(path_parts) == 2:  # Regular nested resource
                        main_res, sub_res = path_parts
                        if main_res in data and isinstance(data[main_res], dict) and sub_res in data[main_res]:
                            count = len(data[main_res][sub_res])
                    # Skip global resources when processing regular regions
                else:
                    if resource_path in data:
                        if isinstance(data[resource_path], list):
                            count = len(data[resource_path])
                        elif isinstance(data[resource_path], dict):
                            # For services returning a dict with multiple resource types
                            count = sum(len(val) for val in data[resource_path].values() if isinstance(val, list))
                
                row[resource_name] = count
                total_by_type[resource_name] += count
                region_total += count
            
            row['Total'] = region_total
            region_rows.append(row)
        
        # Handle global services
        if 'global_services' in self.results:
            row = {'Region': 'global'}
            region_total = 0
            
            for resource_name, resource_path in resource_types:
                count = 0
                if resource_path.startswith('global_services'):
                    path_parts = resource_path.split('.')
                    if len(path_parts) == 3:  # global_services.service.resource format
                        _, service, resource = path_parts  # Use _ for the first part since we know it's "global_services"
                        if (service in self.results['global_services'] and 
                                resource in self.results['global_services'][service]):
                            count = len(self.results['global_services'][service][resource])
                    
                    row[resource_name] = count
                    total_by_type[resource_name] = total_by_type.get(resource_name, 0) + count
                    region_total += count
            
            row['Total'] = region_total
            region_rows.append(row)
        
        # Add totals row
        totals_row = {'Region': 'TOTAL'}
        grand_total = 0
        
        for resource_name in total_by_type:
            totals_row[resource_name] = total_by_type[resource_name]
            grand_total += total_by_type[resource_name]
        
        totals_row['Total'] = grand_total
        region_rows.append(totals_row)
        
        # Write to Excel
        if region_rows:
            df = pd.DataFrame(region_rows)
            df.to_excel(writer, sheet_name='Resource Usage by Region', index=False)
            self._format_sheet(writer.sheets['Resource Usage by Region'], df, header_format)

    def _write_summary(self, writer: pd.ExcelWriter, header_format: Any) -> None:
        """Write overall summary information."""
        self._write_resource_counts(writer, header_format)
    
    def _write_resource_counts(self, writer: pd.ExcelWriter, header_format: Any) -> None:
        """Write a summary of resource counts across all regions."""
        resource_counts = []
        
        try:
            # Handle global services
            if 'global_services' in self.results:
                # Add IAM resources
                if 'iam' in self.results['global_services']:
                    iam_data = self.results['global_services']['iam']
                    
                    # Get counts for IAM resources
                    users = iam_data.get('users', [])
                    roles = iam_data.get('roles', [])
                    groups = iam_data.get('groups', [])
                    
                    # Make sure these are lists before counting
                    if not isinstance(users, list): users = []
                    if not isinstance(roles, list): roles = []
                    if not isinstance(groups, list): groups = []
                    
                    resource_counts.extend([
                        {'Category': 'IAM Users', 'Count': len(users)},
                        {'Category': 'IAM Roles', 'Count': len(roles)},
                        {'Category': 'IAM Groups', 'Count': len(groups)}
                    ])
                
                # Route53 resources
                if 'route53' in self.results['global_services']:
                    route53_data = self.results['global_services']['route53']
                    if isinstance(route53_data, dict):  # Check if it's a dictionary
                        # Get counts for Route53 resources safely
                        hosted_zones = route53_data.get('hosted_zones', [])
                        health_checks = route53_data.get('health_checks', [])
                        traffic_policies = route53_data.get('traffic_policies', [])
                        if not isinstance(traffic_policies, list):
                            print(f"WARNING: traffic_policies is not a list: {type(traffic_policies)}")
                            traffic_policies = []
                        
                        zone_records = route53_data.get('zone_records', [])
                        if not isinstance(zone_records, list):
                            print(f"WARNING: zone_records is not a list: {type(zone_records)}")
                            zone_records = []
                        
                        resource_counts.extend([
                            {'Category': 'Route53 Hosted Zones', 'Count': len(hosted_zones)},
                            {'Category': 'Route53 Health Checks', 'Count': len(health_checks)},
                            {'Category': 'Route53 Traffic Policies', 'Count': len(traffic_policies)},
                            {'Category': 'Route53 Zone Records', 'Count': len(zone_records)}
                        ])
            
            # Regional resources
            if 'regions' in self.results:
                # Initialize counters
                ec2_count = 0
                rds_count = 0
                lambda_count = 0
                dynamodb_count = 0
                bedrock_count = 0
                vpc_count = 0
                s3_count = 0
                fsx_count = 0
                asg_count = 0
                launch_config_count = 0
                launch_template_count = 0
                target_group_count = 0
                load_balancer_count = 0
                config_recorder_count = 0
                config_rule_count = 0
                config_conformance_pack_count = 0
                config_aggregator_count = 0
                sns_count = 0
                sns_topic_count = 0
                sns_subscription_count = 0
                dms_replication_instances_count = 0
                dms_replication_tasks_count = 0
                dms_endpoints_count = 0
                dms_subnet_groups_count = 0
                
                # Count resources across all regions
                for region, services in self.results['regions'].items():
                    if 'ec2' in services:
                        ec2_count += len(services['ec2'])
                    if 'rds' in services:
                        rds_count += len(services['rds'])
                    if 'lambda' in services:
                        lambda_count += len(services['lambda'])
                    if 'dynamodb' in services:
                        dynamodb_count += len(services['dynamodb'])
                    if 'bedrock' in services:
                        bedrock_count += len(services['bedrock'])
                    if 'vpc' in services:
                        vpc_count += len(services['vpc'])
                    if 's3' in services:
                        s3_count += len(services['s3'])
                    if 'fsx' in services:
                        fsx_count += len(services['fsx'])
                    
                    # Count autoscaling resources
                    if 'autoscaling' in services and isinstance(services['autoscaling'], dict):
                        autoscaling_data = services['autoscaling']
                        asg_count += len(autoscaling_data.get('auto_scaling_groups', []))
                        launch_config_count += len(autoscaling_data.get('launch_configurations', []))
                        launch_template_count += len(autoscaling_data.get('launch_templates', []))
                        target_group_count += len(autoscaling_data.get('target_groups', []))
                        load_balancer_count += len(autoscaling_data.get('load_balancers', []))
                    
                    # Count Config resources
                    if 'config' in services and isinstance(services['config'], dict):
                        config_data = services['config']
                        config_recorder_count += len(config_data.get('recorders', []))
                        config_rule_count += len(config_data.get('rules', []))
                        config_conformance_pack_count += len(config_data.get('conformance_packs', []))
                        config_aggregator_count += len(config_data.get('aggregators', []))
                    
                    if 'sns' in services:
                        sns_count += len(services['sns'])
                        for topic in services['sns']:
                            sns_topic_count += 1
                            sns_subscription_count += topic.get('Subscription Count', 0)
                    
                    # Count DMS resources
                    if 'dms' in services and isinstance(services['dms'], dict):
                        dms_data = services['dms']
                        dms_replication_instances_count += len(dms_data.get('replication_instances', []))
                        dms_replication_tasks_count += len(dms_data.get('replication_tasks', []))
                        dms_endpoints_count += len(dms_data.get('endpoints', []))
                        dms_subnet_groups_count += len(dms_data.get('replication_subnet_groups', []))
                
                # Add counts to the resource_counts list
                resource_counts.extend([
                    {'Category': 'EC2 Instances', 'Count': ec2_count},
                    {'Category': 'RDS Instances', 'Count': rds_count},
                    {'Category': 'Lambda Functions', 'Count': lambda_count},
                    {'Category': 'DynamoDB Tables', 'Count': dynamodb_count},
                    {'Category': 'Bedrock Models', 'Count': bedrock_count},
                    {'Category': 'VPCs', 'Count': vpc_count},
                    {'Category': 'S3 Buckets', 'Count': s3_count},
                    {'Category': 'FSx File Systems', 'Count': fsx_count},
                    {'Category': 'Auto Scaling Groups', 'Count': asg_count},
                    {'Category': 'Launch Configurations', 'Count': launch_config_count},
                    {'Category': 'Launch Templates', 'Count': launch_template_count},
                    {'Category': 'Target Groups', 'Count': target_group_count},
                    {'Category': 'Load Balancers', 'Count': load_balancer_count},
                    {'Category': 'Config Recorders', 'Count': config_recorder_count},
                    {'Category': 'Config Rules', 'Count': config_rule_count},
                    {'Category': 'Config Conformance Packs', 'Count': config_conformance_pack_count},
                    {'Category': 'Config Aggregators', 'Count': config_aggregator_count},
                    {'Category': 'SNS Topics', 'Count': sns_topic_count},
                    {'Category': 'SNS Subscriptions', 'Count': sns_subscription_count}
                ])
            
            # Write the summary data
            if resource_counts:
                self._write_dataframe(writer, 'Resource Counts', resource_counts, header_format)
                
        except Exception as e:
            print(f"Error in _write_resource_counts: {str(e)}")
            print(traceback.format_exc())

    def _format_sheet(self, worksheet, dataframe, header_format):
        """Format Excel worksheet with headers and column widths."""
        # Format the header row with the header format
        for col_num, value in enumerate(dataframe.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Set column widths based on content
        for idx, col in enumerate(dataframe.columns):
            # Calculate max width based on column name and values
            max_len = len(str(col)) + 2  # Add padding
            
            # Check values in the column
            for i, value in enumerate(dataframe[col]):
                if value is not None:
                    # Get string representation and calculate length
                    str_value = str(value)
                    cell_len = len(str_value)
                    
                    # Limit max width to avoid excessive column widths
                    if cell_len > 50:
                        cell_len = 50
                    
                    max_len = max(max_len, cell_len)
            
            # Set column width
            worksheet.set_column(idx, idx, max_len)

class Report:
    def __init__(self):
        self.resource_types = {
            'ec2': 'EC2 Instances',
            'rds': 'RDS Instances',
            'lambda': 'Lambda Functions',
            'dynamodb': 'DynamoDB Tables',
            'bedrock': 'Bedrock Models',
            's3': 'S3 Buckets',
            'fsx': 'FSx',
            'SNS Topic': 'SNS'
        }
        
    def create_resource_usage_sheet(self, workbook, data):
        services = [
            'ec2',
            'rds',
            'lambda',
            'dynamodb',
            'bedrock',
            's3',
            'fsx',
            'SNS'
        ]

