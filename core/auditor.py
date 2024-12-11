from typing import List, Dict, Any
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from services.base import AWSService
from services.ec2 import EC2Service
from services.quicksight import QuickSightService
from services.rds import RDSService
from services.vpc import VPCService
from services.lambda_service import LambdaService
from services.dynamodb import DynamoDBService
from services.bedrock import BedrockService
from services.iam import IAMService
from services.s3 import S3Service

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
            if 'ec2' in self.services:
                self.print_progress("  Checking EC2 instances...")
                ec2_service = EC2Service(self.session, region)
                regional_results['ec2'] = ec2_service.audit()
                
            if 'quicksight' in self.services:
                self.print_progress("  Checking QuickSight resources...")
                quicksight_service = QuickSightService(self.session, region)
                regional_results['quicksight'] = quicksight_service.audit()

            if 'rds' in self.services:
                self.print_progress("  Checking RDS instances...")
                rds_service = RDSService(self.session, region)
                regional_results['rds'] = rds_service.audit()

            if 'vpc' in self.services:
                self.print_progress("  Checking VPC resources...")
                vpc_service = VPCService(self.session, region)
                regional_results['vpc'] = vpc_service.audit()

            if 'lambda' in self.services:
                self.print_progress("  Checking Lambda functions...")
                lambda_service = LambdaService(self.session, region)
                regional_results['lambda'] = lambda_service.audit()

            if 'dynamodb' in self.services:
                self.print_progress("  Checking DynamoDB tables...")
                dynamodb_service = DynamoDBService(self.session, region)
                regional_results['dynamodb'] = dynamodb_service.audit()

            if 'bedrock' in self.services:
                self.print_progress("  Checking Bedrock resources...")
                bedrock_service = BedrockService(self.session, region)
                regional_results['bedrock'] = bedrock_service.audit()

            return regional_results
            
        except Exception as e:
            print(f"Error in region {region}: {str(e)}")
            return {'error': str(e)}