from typing import List, Dict, Any
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from services.base import AWSService
from services.amplify import AmplifyService
from services.autoscaling import AutoScalingService
from services.ec2 import EC2Service
from services.rds import RDSService
from services.route53 import Route53Service
from services.vpc import VPCService
from services.lambda_service import LambdaService
from services.lightsail import LightsailService
from services.dynamodb import DynamoDBService
from services.bedrock import BedrockService
from services.iam import IAMService
from services.s3 import S3Service
from services.glue import GlueService
from services.athena import AthenaService
from services.fsx import FSxService
from services.config import ConfigService

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
        
        # Make Route53 the first global service to audit
        if 'route53' in self.services:
            self.print_progress("\nAuditing Route53 resources...")
            try:
                route53_service = Route53Service(self.session)
                print("Created Route53Service instance")  # Debug
                
                route53_results = route53_service.audit()
                print(f"Route53 audit completed with keys: {route53_results.keys()}")  # Debug
                
                # Check if we have any actual data
                has_data = any(len(resources) > 0 for resources in route53_results.values())
                if has_data:
                    print(f"Route53 has data, adding to global services")  # Debug
                    global_results['route53'] = route53_results
                else:
                    print("No Route53 data found")  # Debug
                    # Add empty data structure to ensure it appears in reports
                    global_results['route53'] = {
                        'hosted_zones': [],
                        'health_checks': [],
                        'traffic_policies': []
                    }
            except Exception as e:
                print(f"Error in Route53 audit: {str(e)}")  # Debug
                # Add empty data structure even on error
                global_results['route53'] = {
                    'hosted_zones': [],
                    'health_checks': [],
                    'traffic_policies': []
                }

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
                        if 'autoscaling' in result and isinstance(result['autoscaling'], dict):
                            autoscaling_data = result['autoscaling']
                            self.print_progress(f"    Auto Scaling Groups: {len(autoscaling_data.get('auto_scaling_groups', []))}")
                            self.print_progress(f"    Launch Configurations: {len(autoscaling_data.get('launch_configurations', []))}")
                            self.print_progress(f"    Launch Templates: {len(autoscaling_data.get('launch_templates', []))}")
                            self.print_progress(f"    Target Groups: {len(autoscaling_data.get('target_groups', []))}")
                            self.print_progress(f"    Load Balancers: {len(autoscaling_data.get('load_balancers', []))}")
                        
                        if 'config' in result and isinstance(result['config'], dict):
                            config_data = result['config']
                            self.print_progress(f"    Config Recorders: {len(config_data.get('recorders', []))}")
                            self.print_progress(f"    Config Rules: {len(config_data.get('rules', []))}")
                            self.print_progress(f"    Conformance Packs: {len(config_data.get('conformance_packs', []))}")
                            self.print_progress(f"    Config Aggregators: {len(config_data.get('aggregators', []))}")
                        
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
            service_map = {
                'amplify': AmplifyService,
                'athena': AthenaService,
                'autoscaling': AutoScalingService,
                'bedrock': BedrockService,
                'config': ConfigService,
                'dynamodb': DynamoDBService,
                'ec2': EC2Service,
                'fsx': FSxService,
                'glue': GlueService,
                'iam': IAMService,
                'lambda': LambdaService,
                'lightsail': LightsailService,
                'rds': RDSService,
                'route53': Route53Service,
                's3': S3Service,
                'vpc': VPCService
            }
            for service in self.services:
                try:
                    self.print_progress(f"  Checking {service}...")
                    if service in service_map:
                        service_instance = service_map[service](self.session, region)
                        regional_results[service] = service_instance.audit()
                except Exception as service_error:
                    self.print_progress(f"Error in {service} service for region {region}: {str(service_error)}")
                    regional_results[service] = {'error': str(service_error)}
                    continue

            return regional_results
            
        except Exception as e:
            self.print_progress(f"Error in region {region}: {str(e)}")
            return {'error': str(e)}