#!/usr/bin/env python3
import argparse
import boto3
import os
from core.auditor import AWSAuditor
from core.report import ReportGenerator
from config.settings import AVAILABLE_SERVICES, DEFAULT_MAX_WORKERS, DEFAULT_SERVICES

def parse_arguments():
    parser = argparse.ArgumentParser(description='AWS Resource Audit Tool')
    parser.add_argument('--profile', type=str,
                       help='AWS profile name to use (default: "default")',
                       default='default')
    parser.add_argument(
        '--regions',
        type=str,  # Change this to string
        help='Comma-separated list of AWS regions to audit (default: all regions)',
        default='all'
    )
    parser.add_argument('--services', 
                       type=str,
                       default=','.join(DEFAULT_SERVICES),  # Use the list from settings.py
                       help='AWS services to audit')
    parser.add_argument('--output-dir', type=str,
                       help='Directory for output files (default: "results")',
                       default='results')
    
    args = parser.parse_args()
    return args

def get_regions(session: boto3.Session, regions_arg: str) -> list:
    ec2 = session.client('ec2')
    available_regions = [r['RegionName'] for r in ec2.describe_regions()['Regions']]
    
    if regions_arg.lower() == 'all':
        return available_regions
        
    requested_regions = regions_arg.split(',')
    invalid_regions = [r for r in requested_regions if r not in available_regions]
    
    if invalid_regions:
        raise ValueError(f"Invalid regions: {', '.join(invalid_regions)}")
        
    return requested_regions

def main():
    args = parse_arguments()
    
    try:
        # Create session with profile and default region
        session = boto3.Session(
            profile_name=args.profile,
            region_name='us-east-1'  # Set a default region for initial client creation
        )
        # Test the session
        sts = session.client('sts')
        sts.get_caller_identity()
    except Exception as e:
        print(f"Error with AWS credentials: {str(e)}")
        return 1

    try:
        # Always get regions list, defaulting to 'all' if not specified
        regions = get_regions(session, args.regions or 'all')
        print(f"Using regions: {regions}")
        
        # Handle services parameter
        if args.services == 'all':
            services = AVAILABLE_SERVICES
        else:
            services = args.services.lower().split(',')
        print(f"Auditing services: {services}")
        
        # Initialize auditor with both parameters
        print(f"Debug - Creating AWSAuditor with regions={regions} and services={services}")
        auditor = AWSAuditor(session, regions=regions, services=services)
        results = auditor.run_audit(max_workers=DEFAULT_MAX_WORKERS)
        
        output_dir = args.output_dir
        print(f"Saving results to: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        report_generator = ReportGenerator(results, output_dir)
        report_generator.generate_reports()
        
    except Exception as e:
        print(f"Error during audit: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())