class AWSAuditorError(Exception):
    """Base exception class for AWS Auditor"""
    pass

class RegionError(AWSAuditorError):
    """Exception raised for region-related errors"""
    pass

class ServiceError(AWSAuditorError):
    """Exception raised for service-related errors"""
    pass

class AuthenticationError(AWSAuditorError):
    """Exception raised for AWS authentication errors"""
    pass

class ResourceAccessError(AWSAuditorError):
    """Exception raised when unable to access AWS resources"""
    pass

class ReportGenerationError(AWSAuditorError):
    """Exception raised when report generation fails"""
    pass