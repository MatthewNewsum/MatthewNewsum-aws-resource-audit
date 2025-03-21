from collections import defaultdict
from typing import Any, Dict, List
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from config.settings import AVAILABLE_SERVICES
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

    def _write_regional_resources(self, writer: pd.ExcelWriter, header_format):
        regional_data = defaultdict(list)
        
        for region, data in self.results['regions'].items():
            for service, resources in data.items():
                if not resources:
                    continue
                    
                if service == 'glue':
                    # Handle glue service which has nested structure
                    if 'databases' in resources:
                        for db in resources['databases']:
                            db['Region'] = region
                            regional_data['Glue Databases'].append(db)
                    if 'jobs' in resources:
                        for job in resources['jobs']:
                            job['Region'] = region
                            regional_data['Glue Jobs'].append(job)
                    if 'crawlers' in resources:
                        for crawler in resources['crawlers']:
                            crawler['Region'] = region
                            regional_data['Glue Crawlers'].append(crawler)
                elif service == 'athena':
                    # Handle athena service which has nested structure
                    if 'workgroups' in resources:
                        for wg in resources['workgroups']:
                            wg['Region'] = region
                            regional_data['Athena Workgroups'].append(wg)
                    if 'named_queries' in resources:
                        for query in resources['named_queries']:
                            query['Region'] = region
                            regional_data['Athena Named Queries'].append(query)
                    if 'data_catalogs' in resources:
                        for catalog in resources['data_catalogs']:
                            catalog['Region'] = region
                            regional_data['Athena Data Catalogs'].append(catalog)
                else:
                    # Handle other services as before
                    for resource in resources:
                        if isinstance(resource, dict):
                            resource['Region'] = region
                            regional_data[f'{service.upper()} {self._get_resource_type(service)}'].append(resource)

        # Write each resource type to its own worksheet
        for resource_type, resources in regional_data.items():
            if resources:
                df = pd.DataFrame(resources)
                df.to_excel(writer, sheet_name=resource_type, index=False)
                self._format_worksheet(writer, resource_type, df, header_format)
                print(f"  Added {len(resources)} {resource_type}")

    def _write_resource_usage_by_region(self, writer: pd.ExcelWriter, header_format: Any):
        usage_data = []
        # Get services from config
        services = {
            service.upper(): service.lower() 
            for service in AVAILABLE_SERVICES
        }
        
        for region in self.results.get('regions', {}):
            row = {'Region': region}
            for service_name, service_key in services.items():
                resources = self.results['regions'][region].get(service_key, [])
                row[service_name] = '✓' if resources and len(resources) > 0 else '-'
            usage_data.append(row)
            
        self._write_dataframe(writer, 'Resource Usage by Region', usage_data, header_format)

    def _write_summary(self, writer: pd.ExcelWriter, header_format: Any):
        self._write_resource_counts(writer, header_format)

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
                'Bedrock Models': len(data.get('bedrock', [])),
                'Glue Resources': len(data.get('glue', [])),
            })
        self._write_dataframe(writer, 'Region Details', region_details, header_format)

    def _write_resource_counts(self, writer: pd.ExcelWriter, header_format):
        resource_counts = []
        
        for region, data in self.results['regions'].items():
            for service, resources in data.items():
                if service == 'glue':
                    # Handle glue service counts
                    resource_counts.extend([
                        {'Category': 'Glue Databases', 'Count': len(resources.get('databases', []))},
                        {'Category': 'Glue Jobs', 'Count': len(resources.get('jobs', []))},
                        {'Category': 'Glue Crawlers', 'Count': len(resources.get('crawlers', []))}
                    ])
                elif service == 'athena':
                    resource_counts.extend([
                        {'Category': 'Athena Workgroups', 'Count': len(resources.get('workgroups', []))},
                        {'Category': 'Athena Named Queries', 'Count': len(resources.get('named_queries', []))},
                        {'Category': 'Athena Data Catalogs', 'Count': len(resources.get('data_catalogs', []))}
                    ])
                else:
                    # Handle other services as before
                    if resources:
                        count = len(resources)
                        category = f'{service.upper()} {self._get_resource_type(service)}'
                        resource_counts.append({'Category': category, 'Count': count})
        
        df = pd.DataFrame(resource_counts)
        df = df.groupby('Category')['Count'].sum().reset_index()
        df.to_excel(writer, sheet_name='Resource Counts', index=False)
        self._format_worksheet(writer, 'Resource Counts', df, header_format)

    def _get_resource_type(self, service: str) -> str:
        """Map service names to their resource type names for display"""
        resource_types = {
            'ec2': 'Instances',
            'rds': 'Instances',
            'vpc': 'Resources',
            'lambda': 'Functions',
            'lightsail': 'Instances',
            'dynamodb': 'Tables',
            'bedrock': 'Models',
            'amplify': 'Apps',
            's3': 'Buckets',
            'iam': 'Resources',
            'glue': 'Resources',  # This is handled separately in the code
            'athena': 'Resources',  # This is handled separately in the code
        }
        return resource_types.get(service, 'Resources')

    def _format_worksheet(self, writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame, header_format: Any):
        """Format worksheet with headers and column widths"""
        worksheet = writer.sheets[sheet_name]
        
        # Format headers
        for idx, col in enumerate(df.columns):
            worksheet.write(0, idx, col, header_format)
            
            # Auto-adjust column width based on content
            max_length = max(
                df[col].astype(str).apply(len).max(),  # Max length of data
                len(str(col))  # Length of column header
            ) + 2  # Add some padding
            
            worksheet.set_column(idx, idx, max_length)

        # Freeze the header row
        worksheet.freeze_panes(1, 0)