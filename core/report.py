import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
import json
import os
import xlsxwriter

class ReportGenerator:
    def __init__(self, results: Dict[str, Any], output_dir: str):
        self.results = results
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    def generate_reports(self):
        print("\nGenerating reports...")
        json_path = self._save_json_report()
        print(f"\nJSON report saved to: {json_path}")
        
        print("\nGenerating Excel report...")
        excel_path = self._generate_excel_report()
        print(f"Excel report saved to: {excel_path}")
        
        print("\nAudit complete!")

    def _save_json_report(self) -> str:
        json_path = os.path.join(self.output_dir, f'aws_inventory_{self.timestamp}.json')
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        return json_path

    def _generate_excel_report(self) -> str:
        excel_path = os.path.join(self.output_dir, f'aws_inventory_{self.timestamp}.xlsx')
        
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            workbook = writer.book
            header_format = self._get_header_format(workbook)
            
            self._write_global_resources(writer, header_format)
            self._write_regional_resources(writer, header_format)
            self._write_resource_usage_by_region(writer, header_format)
            self._write_summary(writer, header_format)

        return excel_path

    def _get_header_format(self, workbook: xlsxwriter.Workbook) -> Any:
        return workbook.add_format({
            'bold': True,
            'bg_color': '#0066cc',
            'font_color': 'white',
            'border': 1
        })

    def _write_dataframe(self, writer: pd.ExcelWriter, sheet_name: str, 
                        data: List[Dict[str, Any]], header_format: Any):
        if not data:
            return

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        worksheet = writer.sheets[sheet_name]
        for idx, col in enumerate(df.columns):
            worksheet.write(0, idx, col, header_format)
            worksheet.set_column(idx, idx, len(str(col)) + 2)
        
        print(f"  Added {len(data)} {sheet_name}")

    def _write_global_resources(self, writer: pd.ExcelWriter, header_format: Any):
        if 'global_services' in self.results:
            if 'iam' in self.results['global_services']:
                iam_data = self.results['global_services']['iam']
                if 'users' in iam_data:
                    self._write_dataframe(writer, 'IAM Users', iam_data['users'], header_format)
                if 'roles' in iam_data:
                    self._write_dataframe(writer, 'IAM Roles', iam_data['roles'], header_format)
                if 'groups' in iam_data:
                    self._write_dataframe(writer, 'IAM Groups', iam_data['groups'], header_format)
            
            if 's3' in self.results['global_services']:
                self._write_dataframe(writer, 'S3 Buckets', 
                                    self.results['global_services']['s3'],
                                    header_format)

    def _write_regional_resources(self, writer: pd.ExcelWriter, header_format: Any):
        regional_data = {
            'EC2 Instances': [],
            'Quicksight Resources': [],
            'RDS Instances': [],
            'VPCs': [],
            'Subnets': [],
            'Internet Gateways': [],
            'Routes': [],
            'Security Groups': [],
            'Security Group Rules': [],
            'Lambda Functions': [],
            'DynamoDB Tables': [],
            'Bedrock Models': []
        }

        for region_data in self.results.get('regions', {}).values():
            for service, data in region_data.items():
                if isinstance(data, list):
                    if service == 'ec2':
                        regional_data['EC2 Instances'].extend(data)
                    elif service == 'quicksight':
                        regional_data['QuickSight Resources'].extend(data)
                    elif service == 'rds':
                        regional_data['RDS Instances'].extend(data)
                    elif service == 'vpc':
                        for vpc in data:
                            regional_data['VPCs'].append({k: v for k, v in vpc.items() 
                                                        if not isinstance(v, (list, dict))})
                            if 'subnets' in vpc:
                                regional_data['Subnets'].extend(vpc['subnets'])
                            if 'internet_gateways' in vpc:
                                regional_data['Internet Gateways'].extend(vpc['internet_gateways'])
                            if 'route_tables' in vpc:
                                regional_data['Routes'].extend(vpc['route_tables'])
                            if 'security_groups' in vpc:
                                regional_data['Security Groups'].extend(vpc['security_groups'])
                            if 'security_group_rules' in vpc:
                                regional_data['Security Group Rules'].extend(vpc['security_group_rules'])
                    elif service == 'lambda':
                        regional_data['Lambda Functions'].extend(data)
                    elif service == 'dynamodb':
                        regional_data['DynamoDB Tables'].extend(data)
                    elif service == 'bedrock':
                        regional_data['Bedrock Models'].extend(data)

        for sheet_name, data in regional_data.items():
            if data:
                self._write_dataframe(writer, sheet_name, data, header_format)

    def _write_resource_usage_by_region(self, writer: pd.ExcelWriter, header_format: Any):
        usage_data = []
        services = {
            'EC2': 'ec2',
            'RDS': 'rds', 
            'VPC': 'vpc',
            'Lambda': 'lambda',
            'DynamoDB': 'dynamodb',
            'Bedrock': 'bedrock'
        }
        
        for region in self.results.get('regions', {}):
            row = {'Region': region}
            for service_name, service_key in services.items():
                resources = self.results['regions'][region].get(service_key, [])
                row[service_name] = '✓' if resources and len(resources) > 0 else '-'
            usage_data.append(row)
            
        self._write_dataframe(writer, 'Resource Usage by Region', usage_data, header_format)

    def _write_summary(self, writer: pd.ExcelWriter, header_format: Any):
        # Resource Counts
        resource_counts = [
            {'Category': 'Regions Found', 'Count': len(self.results.get('regions', {}))},
            {'Category': 'EC2 Instances', 'Count': sum(len(r.get('ec2', [])) for r in self.results['regions'].values())},
            {'Category': 'QuickSight Resources', 'Count': sum(len(r.get('quicksight', [])) for r in self.results['regions'].values())},
            {'Category': 'RDS Instances', 'Count': sum(len(r.get('rds', [])) for r in self.results['regions'].values())},
            {'Category': 'VPC Resources', 'Count': sum(len(r.get('vpc', [])) for r in self.results['regions'].values())},
            {'Category': 'Lambda Functions', 'Count': sum(len(r.get('lambda', [])) for r in self.results['regions'].values())},
            {'Category': 'DynamoDB Tables', 'Count': sum(len(r.get('dynamodb', [])) for r in self.results['regions'].values())},
            {'Category': 'Bedrock Models', 'Count': sum(len(r.get('bedrock', [])) for r in self.results['regions'].values())},
            {'Category': 'IAM Users', 'Count': len(self.results.get('global_services', {}).get('iam', {}).get('users', []))},
            {'Category': 'IAM Roles', 'Count': len(self.results.get('global_services', {}).get('iam', {}).get('roles', []))},
            {'Category': 'IAM Groups', 'Count': len(self.results.get('global_services', {}).get('iam', {}).get('groups', []))},
            {'Category': 'S3 Buckets', 'Count': len(self.results.get('global_services', {}).get('s3', []))}
        ]
        self._write_dataframe(writer, 'Resource Counts', resource_counts, header_format)

        # Region Summary
        successful_regions = [r for r in self.results['regions'].values() if 'error' not in r]
        failed_regions = [r for r in self.results['regions'].values() if 'error' in r]
        
        region_summary = [
            {'Category': 'Total Regions', 'Count': len(self.results.get('regions', {}))},
            {'Category': 'Successful Regions', 'Count': len(successful_regions)},
            {'Category': 'Failed Regions', 'Count': len(failed_regions)}
        ]
        self._write_dataframe(writer, 'Region Summary', region_summary, header_format)

        # Per-Region Details
        region_details = []
        for region, data in self.results.get('regions', {}).items():
            region_details.append({
                'Region': region,
                'EC2 Instances': len(data.get('ec2', [])),
                'RDS Instances': len(data.get('rds', [])),
                'VPCs': len(data.get('vpc', [])),
                'Lambda Functions': len(data.get('lambda', [])),
                'DynamoDB Tables': len(data.get('dynamodb', [])),
                'Bedrock Models': len(data.get('bedrock', []))
            })
        self._write_dataframe(writer, 'Region Details', region_details, header_format)