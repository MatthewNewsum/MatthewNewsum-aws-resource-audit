from typing import Dict, List, Any
from .base import AWSService

class GlueService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('glue', region_name=region)
        
    @property
    def service_name(self) -> str:
        return 'glue'

    def audit(self) -> Dict[str, List[Dict[str, Any]]]:
        try:
            return {
                'databases': self._audit_databases(),
                'jobs': self._audit_jobs(),
                'crawlers': self._audit_crawlers()
            }
        except Exception as e:
            print(f"Error auditing Glue in {self.region}: {str(e)}")
            return {
                'databases': [],
                'jobs': [],
                'crawlers': []
            }

    def _audit_databases(self) -> List[Dict[str, Any]]:
        databases = []
        paginator = self.client.get_paginator('get_databases')
        for page in paginator.paginate():
            for db in page.get('DatabaseList', []):
                databases.append({
                    'Name': db['Name'],
                    'Description': db.get('Description', 'N/A'),
                    'LocationUri': db.get('LocationUri', 'N/A'),
                    'CreateTime': str(db.get('CreateTime', 'N/A'))
                })
        return databases

    def _audit_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        paginator = self.client.get_paginator('get_jobs')
        for page in paginator.paginate():
            for job in page.get('Jobs', []):
                jobs.append({
                    'Name': job['Name'],
                    'Role': job.get('Role', 'N/A'),
                    'CreatedOn': str(job.get('CreatedOn', 'N/A')),
                    'LastModifiedOn': str(job.get('LastModifiedOn', 'N/A')),
                    'Type': job.get('Command', {}).get('Name', 'N/A'),
                    'WorkerType': job.get('WorkerType', 'N/A'),
                    'NumberOfWorkers': job.get('NumberOfWorkers', 'N/A')
                })
        return jobs

    def _audit_crawlers(self) -> List[Dict[str, Any]]:  # Fixed type hint syntax
        crawlers = []
        paginator = self.client.get_paginator('get_crawlers')
        for page in paginator.paginate():
            for crawler in page.get('Crawlers', []):
                crawlers.append({
                    'Name': crawler['Name'],
                    'Role': crawler.get('Role', 'N/A'),
                    'DatabaseName': crawler.get('DatabaseName', 'N/A'),
                    'State': crawler.get('State', 'N/A'),
                    'Schedule': crawler.get('Schedule', 'N/A'),
                    'LastUpdated': str(crawler.get('LastUpdated', 'N/A'))
                })
        return crawlers