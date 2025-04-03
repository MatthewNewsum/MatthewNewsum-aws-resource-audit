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

    def _write_resource_usage_by_region(self, writer: pd.ExcelWriter, header_format: Any) -> None:
        """Write resource usage by region matrix."""
        print("Writing resource usage by region...")
        
        # Collect all resource types and regions
        regions = []
        resource_counts = {}
        
        for region, services in self.results['regions'].items():
            regions.append(region)
            
            # Add these lines to track autoscaling resources
            if 'autoscaling' in services and isinstance(services['autoscaling'], dict):
                autoscaling_data = services['autoscaling']
                resource_counts.setdefault(region, {})
                
                # Count auto scaling groups
                if 'auto_scaling_groups' in autoscaling_data:
                    resource_counts[region]['Auto Scaling Groups'] = len(autoscaling_data['auto_scaling_groups'])
                
                # Count launch configurations
                if 'launch_configurations' in autoscaling_data:
                    resource_counts[region]['Launch Configurations'] = len(autoscaling_data['launch_configurations'])
                
                # Count launch templates
                if 'launch_templates' in autoscaling_data:
                    resource_counts[region]['Launch Templates'] = len(autoscaling_data['launch_templates'])
                
                # Count target groups
                if 'target_groups' in autoscaling_data:
                    resource_counts[region]['Target Groups'] = len(autoscaling_data['target_groups'])
                
                # Count load balancers
                if 'load_balancers' in autoscaling_data:
                    resource_counts[region]['Load Balancers'] = len(autoscaling_data['load_balancers'])
            
            # Rest of the existing code for other services...
            usage = {'Region': region}
            
            # Count EC2 instances
            if 'ec2' in services:
                usage['EC2 Instances'] = len(services['ec2'])
            
            # Count RDS instances
            if 'rds' in services:
                usage['RDS Instances'] = len(services['rds'])
            
            # Count Lambda functions
            if 'lambda' in services:
                usage['Lambda Functions'] = len(services['lambda'])
            
            # Count DynamoDB tables
            if 'dynamodb' in services:
                usage['DynamoDB Tables'] = len(services['dynamodb'])
            
            # Count Bedrock models
            if 'bedrock' in services:
                usage['Bedrock Models'] = len(services['bedrock'])
            
            # Add VPC resources - handle the special structure for VPC data
            if 'vpc' in services:
                vpc_count = len(services['vpc'])
                usage['VPCs'] = vpc_count
                
                # If you need more VPC-specific counts
                if vpc_count > 0:
                    for vpc in services['vpc']:
                        if 'Subnet Count' in vpc:
                            usage['Subnets'] = usage.get('Subnets', 0) + vpc['Subnet Count']
                        if 'Security Groups' in vpc:
                            usage['Security Groups'] = usage.get('Security Groups', 0) + vpc['Security Groups']
            
            # Add FSx resources
            if 'fsx' in services:
                usage['FSx'] = len(services['fsx'])
            
            # Add other resource types as needed
            
            resource_counts[region] = usage
        
        if resource_counts:
            self._write_dataframe(writer, 'Resource Usage by Region', resource_counts, header_format)

    def _write_summary(self, writer: pd.ExcelWriter, header_format: Any) -> None:
        """Write overall summary information."""
        self._write_resource_counts(writer, header_format)
    
    def _write_resource_counts(self, writer: pd.ExcelWriter, header_format: Any) -> None:
        """Write a summary of resource counts across all regions."""
        resource_counts = []
        
        try:
            # Handle global services
            if 'global_services' in self.results:
                # Route53 resources
                if 'route53' in self.results['global_services']:
                    route53_data = self.results['global_services']['route53']
                    if isinstance(route53_data, dict):  # Check if it's a dictionary
                        # Get counts for Route53 resources safely
                        hosted_zones = route53_data.get('hosted_zones', [])
                        health_checks = route53_data.get('health_checks', [])
                        traffic_policies = route53_data.get('traffic_policies', [])
                        
                        # Ensure these are actually lists before getting their length
                        if not isinstance(hosted_zones, list):
                            print(f"WARNING: hosted_zones is not a list: {type(hosted_zones)}")
                            hosted_zones = []
                        if not isinstance(health_checks, list):
                            print(f"WARNING: health_checks is not a list: {type(health_checks)}")
                            health_checks = []
                        if not isinstance(traffic_policies, list):
                            print(f"WARNING: traffic_policies is not a list: {type(traffic_policies)}")
                            traffic_policies = []
                        
                        resource_counts.extend([
                            {'Category': 'Route53 Hosted Zones', 'Count': len(hosted_zones)},
                            {'Category': 'Route53 Health Checks', 'Count': len(health_checks)},
                            {'Category': 'Route53 Traffic Policies', 'Count': len(traffic_policies)}
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
                
                # Add counts to the resource_counts list
                resource_counts.extend([
                    {'Category': 'EC2 Instances', 'Count': ec2_count},
                    {'Category': 'RDS Instances', 'Count': rds_count},
                    {'Category': 'Lambda Functions', 'Count': lambda_count},
                    {'Category': 'DynamoDB Tables', 'Count': dynamodb_count},
                    {'Category': 'Bedrock Models', 'Count': bedrock_count},
                    {'Category': 'VPCs', 'Count': vpc_count},
                    {'Category': 'S3 Buckets', 'Count': s3_count},
                    {'Category': 'FSx', 'Count': fsx_count}
                ])
            
            # Write the summary data
            if resource_counts:
                self._write_dataframe(writer, 'Resource Summary', resource_counts, header_format)
                
        except Exception as e:
            print(f"Error in _write_resource_counts: {str(e)}")
            print(traceback.format_exc())