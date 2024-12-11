from typing import Dict, List, Any
from .base import AWSService
from botocore.exceptions import ClientError

class QuickSightService(AWSService):
    @property
    def service_name(self) -> str:
        return 'quicksight'

    def audit(self) -> List[Dict[str, Any]]:
        resources = []
        try:
            # Get AWS account ID from the session
            account_id = self.session.client('sts').get_caller_identity()['Account']
            
            # List all analyses
            analyses = self._list_analyses(account_id)
            for analysis in analyses:
                analysis['Region'] = self.region
                resources.append(analysis)

            # List all dashboards
            dashboards = self._list_dashboards(account_id)
            for dashboard in dashboards:
                dashboard['Region'] = self.region
                resources.append(dashboard)

            # List all datasets
            datasets = self._list_datasets(account_id)
            for dataset in datasets:
                dataset['Region'] = self.region
                resources.append(dataset)

            return resources

        except ClientError as e:
            if 'AccessDeniedException' in str(e):
                print(f"QuickSight not enabled in {self.region}")
                return []
            raise e

    def _list_analyses(self, account_id: str) -> List[Dict[str, Any]]:
        analyses = []
        paginator = self.client.get_paginator('list_analyses')
        
        try:
            for page in paginator.paginate(AwsAccountId=account_id):
                for analysis in page['AnalysisSummaryList']:
                    analyses.append({
                        'Type': 'Analysis',
                        'Name': analysis['Name'],
                        'ID': analysis['AnalysisId'],
                        'Status': analysis['Status'],
                        'LastUpdated': str(analysis.get('LastUpdatedTime')),
                        'Created': str(analysis.get('CreatedTime'))
                    })
        except Exception as e:
            print(f"Error listing analyses: {str(e)}")
        
        return analyses

    def _list_dashboards(self, account_id: str) -> List[Dict[str, Any]]:
        dashboards = []
        paginator = self.client.get_paginator('list_dashboards')
        
        try:
            for page in paginator.paginate(AwsAccountId=account_id):
                for dashboard in page['DashboardSummaryList']:
                    dashboards.append({
                        'Type': 'Dashboard',
                        'Name': dashboard['Name'],
                        'ID': dashboard['DashboardId'],
                        'LastPublished': str(dashboard.get('LastPublishedTime')),
                        'LastUpdated': str(dashboard.get('LastUpdatedTime')),
                        'Created': str(dashboard.get('CreatedTime'))
                    })
        except Exception as e:
            print(f"Error listing dashboards: {str(e)}")
            
        return dashboards

    def _list_datasets(self, account_id: str) -> List[Dict[str, Any]]:
        datasets = []
        paginator = self.client.get_paginator('list_data_sets')
        
        try:
            for page in paginator.paginate(AwsAccountId=account_id):
                for dataset in page['DataSetSummaries']:
                    datasets.append({
                        'Type': 'Dataset',
                        'Name': dataset['Name'],
                        'ID': dataset['DataSetId'],
                        'ImportMode': dataset.get('ImportMode'),
                        'PhysicalTableCount': dataset.get('PhysicalTableCount'),
                        'LastUpdated': str(dataset.get('LastUpdatedTime')),
                        'Created': str(dataset.get('CreatedTime'))
                    })
        except Exception as e:
            print(f"Error listing datasets: {str(e)}")
            
        return datasets