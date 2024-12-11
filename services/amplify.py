from typing import Dict, List, Any
from .base import AWSService

class AmplifyService(AWSService):
    @property
    def service_name(self) -> str:
        return 'amplify'

    def audit(self) -> List[Dict[str, Any]]:
        resources = []
        try:
            paginator = self.client.get_paginator('list_apps')
            for page in paginator.paginate():
                for app in page['apps']:
                    app_details = self._get_app_details(app)
                    if app_details:
                        resources.append(app_details)
        except Exception as e:
            print(f"Error auditing Amplify in {self.region}: {str(e)}")
        return resources

    def _get_app_details(self, app: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return {
                'Region': self.region,
                'App ID': app['appId'],
                'App Name': app['name'],
                'Description': app.get('description', 'N/A'),
                'Repository': app.get('repository', 'N/A'),
                'Platform': app.get('platform', 'N/A'),
                'Status': app.get('status', 'N/A'),
                'Created At': str(app.get('createTime', 'N/A')),
                'Updated At': str(app.get('updateTime', 'N/A')),
                'Framework': app.get('framework', 'N/A'),
                'Custom Domains': ', '.join(self._get_custom_domains(app['appId']))
            }
        except Exception as e:
            print(f"Error processing Amplify app {app.get('name', 'Unknown')}: {str(e)}")
            return None

    def _get_custom_domains(self, app_id: str) -> List[str]:
        try:
            domains = self.client.list_domain_associations(appId=app_id)
            return [domain['domainName'] for domain in domains.get('domainAssociations', [])]
        except:
            return []