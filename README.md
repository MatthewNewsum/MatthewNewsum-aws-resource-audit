# AWS Resource Auditor
# Created by Matt Newsum 
# https://www.linkedin.com/in/mattnewsum/
# http://www.newsum.me

A Python tool for auditing AWS resources across multiple regions and services.

## Companion terraform to create some resources to test this audit app

-Refer to (https://github.com/MatthewNewsum/aws_service_setup_scripts.git) for terraform code to create some resources to test this audit app.

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Prerequisites

- Python 3.6+
- Valid AWS credentials configured (via environment variables, AWS CLI configuration, or IAM role)
- Required Python packages:
  - boto3
  - pandas
  - xlsxwriter

### Known Issues

- The VPC output leaves a lot to be desired - I will try to reformat to be more readable
- Bedrock outputs all enabled models - I will re assess

## Usage

Run the script with optional parameters:

```bash
python main.py [--regions REGIONS] [--services SERVICES] [--output-dir OUTPUT_DIR] [--profile AWS_PROFILE_NAME]
```

### Parameters

- `--regions`: Comma-separated list of AWS regions or "all" (default: "all")
- `--services`: Comma-separated list of services to audit or "all" (default: "all")
- `--output-dir`: Directory for output files (default: "results")
- `--profile`: AWS profile name to use (default: "default")

### Supported AWS Services

- amplify
- athena
- autoscaling
- bedrock
- config
- dynamodb
- ec2
- fsx
- glue
- iam
- kinesis
- lambda
- rds
- route53
- s3
- vpc
- SNS (Simple Notification Service)
  - Topics
  - Subscriptions

### Available Services

- amplify
- athena
- autoscaling
- bedrock
- config
- dynamodb
- ec2
- fsx
- glue
- iam
- kinesis
- lambda
- rds
- route53
- s3
- vpc
- dms

## Examples

Audit all services in all regions:
```bash
python main.py
```

Audit specific services in specific regions:
```bash
python main.py --regions us-east-1,us-west-2 --services ec2,rds,vpc
```

Custom output directory:
```bash
python main.py --output-dir my-audit-results
```
Using a specific AWS profile:
```bash
python main.py --profile matt
## Output

The tool generates two report files:

### 1. JSON Report (`aws_inventory_TIMESTAMP.json`)
- Raw audit data in JSON format
- Complete resource details

### 2. Excel Report (`aws_inventory_TIMESTAMP.xlsx`)
- Formatted spreadsheet with multiple worksheets
- Resource summaries and detailed views
- Regional resource usage matrix

## Excel Report Worksheets
- **Resource Usage by Region**: Shows resource counts by service (Amplify, AutoScaling, Bedrock, DynamoDB, EC2, IAM, Kinesis, Lambda, Lightsail, RDS, S3, SNS, VPC) across all regions
- **Resource Counts**: Summary of total resources by service type
- **Region Summary**: High-level overview of resources per region  
- **Region Details**: Detailed breakdown of all resources by region
- **[Service Name]**: Individual worksheets for each audited service showing detailed resource information

## Error Handling

The tool handles various error scenarios:
- Invalid regions
- Service availability issues
- Authentication/permission problems
- Resource access errors

Errors are logged and included in the final reports.

## Threading

The tool uses concurrent execution for improved performance:
- Default maximum worker threads: 10
- Configurable via source code (DEFAULT_MAX_WORKERS)

