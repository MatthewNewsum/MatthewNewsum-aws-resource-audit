# AWS Service configuration
AVAILABLE_SERVICES = [
    'amplify',
    'bedrock',
    'dynamodb',
    'ec2',
    'iam',
    'lambda',
    'lightsail',
    'rds',
    's3',
    'vpc'
]

# Threading configuration
DEFAULT_MAX_WORKERS = 10

# Excel report configuration
EXCEL_FORMATS = {
    'header': {
        'bold': True,
        'bg_color': '#0066cc',
        'font_color': 'white',
        'border': 1
    }
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'aws_audit.log',
            'formatter': 'standard',
            'level': 'DEBUG'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO'
        }
    }
}

# Error messages
ERROR_MESSAGES = {
    'region_not_enabled': "Region {region} is not enabled for this account",
    'service_not_available': "Service {service} is not available in region {region}",
    'authentication_error': "AWS authentication failed: {error}",
    'permission_error': "Insufficient permissions to access {resource}: {error}"
}