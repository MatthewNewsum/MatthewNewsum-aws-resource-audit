from typing import List, Dict, Any
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from services.base import AWSService
from services.amplify import AmplifyService
from services.ec2 import EC2Service
from services.rds import RDSService
from services.vpc import VPCService
from services.lambda_service import LambdaService
from services.lightsail import LightsailService
from services.dynamodb import DynamoDBService
from services.bedrock import BedrockService
from services.iam import IAMService
from services.s3 import S3Service
from services.glue import GlueService
from services.athena import AthenaService

class AWSAuditor:
    def __init__(self, session: boto3.Session, regions: List[str], services: List[str]):
        self.session = session
        self.regions = regions
        self.services = services
        self.print_lock = Lock()
        self.results = {
            'regions': {},
            'global_services': {}
        }

    def print_progress(self, message):
        with self.print_lock:
            print(message)

    def audit_global_services(self) -> Dict[str, Any]:
        global_results = {}
        
        if 'iam' in self.services:
            self.print_progress("\nAuditing IAM resources...")
            iam_service = IAMService(self.session)
            global_results['iam'] = iam_service.audit()
        
        if 's3' in self.services:
            self.print_progress("\nAuditing S3 buckets...")
            s3_service = S3Service(self.session)
            global_results['s3'] = s3_service.audit()
            
        return global_results

    def run_audit(self, max_workers: int = 10) -> Dict[str, Any]:
        self.print_progress(f"\nAuditing {len(self.regions)} regions: {', '.join(self.regions)}")
        self.print_progress(f"Starting AWS resource audit...")
        self.print_progress(f"Services to audit: {', '.join(self.services)}\n")
        
        self.results['global_services'] = self.audit_global_services()
        processed_regions = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_region = {
                executor.submit(self.audit_region, region): region 
                for region in self.regions
            }
            
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    result = future.result()
                    self.results['regions'][region] = result
                    processed_regions += 1
                    
                    if result:
                        self.print_progress(f"\nResources found in {region}:")
                        self.print_progress(f"    EC2 instances: {len(result.get('ec2', []))}")
                        self.print_progress(f"    RDS instances: {len(result.get('rds', []))}")
                        self.print_progress(f"    VPC resources: {len(result.get('vpc', []))}")
                        self.print_progress(f"    Lambda functions: {len(result.get('lambda', []))}")
                        self.print_progress(f"    DynamoDB tables: {len(result.get('dynamodb', []))}")
                        self.print_progress(f"    Bedrock models: {len(result.get('bedrock', []))}")
                        self.print_progress(f"Successfully processed region: {region}")
                    
                    self.print_progress(f"\nProgress: {processed_regions}/{len(self.regions)} regions processed")
                    
                except Exception as e:
                    self.print_progress(f"Unexpected error processing region {region}: {str(e)}")
                    self.results['regions'][region] = {'error': str(e)}
                    
        return self.results

    def audit_region(self, region: str) -> Dict[str, Any]:
        self.print_progress(f"\nProcessing region: {region}")
        self.print_progress(f"\nAuditing region: {region}")
        regional_results = {}
        
        try:
            for service in self.services:
                try:
                    self.print_progress(f"  Checking {service}...")
                    # Add service-specific handling here
                    if service == 'amplify':
                        service_instance = AmplifyService(self.session, region)
                        regional_results[service] = service_instance.audit()
                    elif service == 'ec2':
                        service_instance = EC2Service(self.session, region)
                        regional_results[service] = service_instance.audit()
                    elif service == 'rds':
                        service_instance = RDSService(self.session, region)
                        regional_results[service] = service_instance.audit()
                    elif service == 'vpc':
                        service_instance = VPCService(self.session, region)
                        regional_results[service] = service_instance.audit()
                    elif service == 'lambda':
                        service_instance = LambdaService(self.session, region)
                        regional_results[service] = service_instance.audit()
                    elif service == 'lightsail':
                        service_instance = LightsailService(self.session, region)
                        regional_results[service] = service_instance.audit()
                    elif service == 'dynamodb':
                        service_instance = DynamoDBService(self.session, region)
                        regional_results[service] = service_instance.audit()
                    elif service == 'bedrock':
                        service_instance = BedrockService(self.session, region)
                        regional_results[service] = service_instance.audit()
                    elif service == 'glue':
                        service_instance = GlueService(self.session, region)
                        regional_results[service] = service_instance.audit()
                    elif service == 'athena':
                        service_instance = AthenaService(self.session, region)
                        regional_results[service] = service_instance.audit()
                except Exception as service_error:
                    self.print_progress(f"Error in {service} service for region {region}: {str(service_error)}")
                    regional_results[service] = {'error': str(service_error)}
                    continue

            return regional_results
            
        except Exception as e:
            self.print_progress(f"Error in region {region}: {str(e)}")
            return {'error': str(e)}