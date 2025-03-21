from typing import Dict, List, Any
from .base import AWSService

class AthenaService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('athena', region_name=region)
        
    @property
    def service_name(self) -> str:
        return 'athena'

    def audit(self) -> Dict[str, List[Dict[str, Any]]]:
        try:
            return {
                'workgroups': self._audit_workgroups(),
                'named_queries': self._audit_named_queries(),
                'data_catalogs': self._audit_data_catalogs()
            }
        except Exception as e:
            print(f"Error auditing Athena in {self.region}: {str(e)}")
            return {
                'workgroups': [],
                'named_queries': [],
                'data_catalogs': []
            }

    def _audit_workgroups(self) -> List[Dict[str, Any]]:
        workgroups = []
        try:
            # Use list_work_groups directly instead of pagination
            response = self.client.list_work_groups()
            for wg in response.get('WorkGroups', []):
                try:
                    details = self.client.get_work_group(WorkGroup=wg['Name'])['WorkGroup']
                    workgroups.append({
                        'Name': details['Name'],
                        'State': details['State'],
                        'Description': details.get('Description', 'N/A'),
                        'CreationTime': str(details['CreationTime']),
                        'EngineVersion': details.get('EngineVersion', {}).get('SelectedEngineVersion', 'N/A'),
                        'OutputLocation': details['Configuration'].get('ResultConfiguration', {}).get('OutputLocation', 'N/A'),
                        'BytesScannedCutoffPerQuery': details['Configuration'].get('BytesScannedCutoffPerQuery', 'N/A'),
                        'EnforceWorkGroupConfiguration': details['Configuration'].get('EnforceWorkGroupConfiguration', False)
                    })
                except Exception as e:
                    print(f"Error getting workgroup details for {wg['Name']}: {str(e)}")
        except Exception as e:
            print(f"Error listing workgroups: {str(e)}")
        return workgroups

    def _audit_named_queries(self) -> List[Dict[str, Any]]:
        named_queries = []
        paginator = self.client.get_paginator('list_named_queries')
        for page in paginator.paginate():
            for query_id in page.get('NamedQueryIds', []):
                try:
                    query = self.client.get_named_query(NamedQueryId=query_id)['NamedQuery']
                    named_queries.append({
                        'Name': query['Name'],
                        'Description': query.get('Description', 'N/A'),
                        'Database': query['Database'],
                        'WorkGroup': query.get('WorkGroup', 'primary'),
                        'QueryString': query['QueryString'][:100] + '...' if len(query['QueryString']) > 100 else query['QueryString']
                    })
                except Exception as e:
                    print(f"Error getting named query details for {query_id}: {str(e)}")
        return named_queries

    def _audit_data_catalogs(self) -> List[Dict[str, Any]]:
        data_catalogs = []
        try:
            paginator = self.client.get_paginator('list_data_catalogs')
            for page in paginator.paginate():
                for catalog in page.get('DataCatalogsSummary', []):
                    data_catalogs.append({
                        'CatalogName': catalog['CatalogName'],
                        'Type': catalog['Type'],
                        'Description': catalog.get('Description', 'N/A')
                    })
        except Exception as e:
            print(f"Error listing data catalogs: {str(e)}")
        return data_catalogs