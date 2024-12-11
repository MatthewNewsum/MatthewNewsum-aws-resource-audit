#!/usr/bin/env python3
import argparse
import boto3
import os
from core.auditor import AWSAuditor
from core.report import ReportGenerator
from config.settings import AVAILABLE_SERVICES, DEFAULT_MAX_WORKERS

def parse_arguments():
    parser = argparse.ArgumentParser(description='AWS Resource Audit Tool')
    parser.add_argument('--regions', type=str, 
                       help='Comma-separated list of regions or "all"',
                       default='all')
    parser.add_argument('--services', type=str, 
                       help=f'Comma-separated list of services {AVAILABLE_SERVICES}',
                       default='all')
    parser.add_argument('--output-dir', type=str,
                       help='Directory for output files',
                       default='results')
    return parser.parse_args()

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
    session = boto3.Session()
    
    try:
        regions = get_regions(session, args.regions)
        services = args.services.lower().split(',') if args.services != 'all' else AVAILABLE_SERVICES
        
        auditor = AWSAuditor(session, regions, services)
        results = auditor.run_audit(max_workers=DEFAULT_MAX_WORKERS)
        
        os.makedirs(args.output_dir, exist_ok=True)
        report_generator = ReportGenerator(results, args.output_dir)
        report_generator.generate_reports()
        
    except Exception as e:
        print(f"Error during audit: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())