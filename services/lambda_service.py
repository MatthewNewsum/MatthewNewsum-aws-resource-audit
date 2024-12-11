from typing import Dict, List, Any
import json
from .base import AWSService

class LambdaService(AWSService):
    @property
    def service_name(self) -> str:
        return 'lambda'

    def audit(self) -> List[Dict[str, Any]]:
        resources = []
        paginator = self.client.get_paginator('list_functions')
        
        for page in paginator.paginate():
            for function in page['Functions']:
                function_details = self._get_function_details(function)
                if function_details:
                    resources.append(function_details)
                    
        return resources

    def _get_function_details(self, function: Dict) -> Dict[str, Any]:
        try:
            policy = self._get_function_policy(function['FunctionName'])
            tags = self._get_function_tags(function['FunctionArn'])
            concurrency = self._get_function_concurrency(function['FunctionName'])
            
            return {
                'Region': self.region,
                'Function Name': function['FunctionName'],
                'ARN': function['FunctionArn'],
                'Runtime': function['Runtime'],
                'Handler': function['Handler'],
                'Code Size': f"{function['CodeSize'] / (1024*1024):.2f} MB",
                'Memory': f"{function['MemorySize']} MB",
                'Timeout': f"{function['Timeout']} seconds",
                'Last Modified': function['LastModified'],
                'Environment Variables': len(function.get('Environment', {}).get('Variables', {})),
                'Layers': len(function.get('Layers', [])),
                'VPC Config': bool(function.get('VpcConfig', {}).get('VpcId')),
                'VPC ID': function.get('VpcConfig', {}).get('VpcId', 'N/A'),
                'Reserved Concurrency': concurrency,
                'Architecture': function.get('Architectures', ['x86_64'])[0],
                'Package Type': function.get('PackageType', 'Zip'),
                'Resource Policy': bool(policy),
                'Tags': self._format_tags(tags)
            }
        except Exception as e:
            print(f"Error processing Lambda function {function['FunctionName']}: {str(e)}")
            return None

    def _get_function_policy(self, function_name: str) -> Dict:
        try:
            policy = self.client.get_policy(FunctionName=function_name)
            return json.loads(policy['Policy'])
        except:
            return {}

    def _get_function_tags(self, function_arn: str) -> Dict:
        try:
            return self.client.list_tags(Resource=function_arn)['Tags']
        except:
            return {}

    def _get_function_concurrency(self, function_name: str) -> str:
        try:
            return self.client.get_function_concurrency(
                FunctionName=function_name
            ).get('ReservedConcurrentExecutions', 'Not configured')
        except:
            return 'Error retrieving'

    def _format_tags(self, tags: Dict) -> str:
        return ', '.join([f"{k}={v}" for k, v in tags.items()]) if tags else 'No Tags'