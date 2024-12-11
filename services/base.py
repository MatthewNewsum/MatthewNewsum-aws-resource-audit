from abc import ABC, abstractmethod
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

class AWSService(ABC):
    def __init__(self, session: boto3.Session, region: str = None):
        self.session = session
        self.region = region
        self.client = self._get_client()

    def _get_client(self):
        """Create boto3 client for the service"""
        return self.session.client(
            self.service_name,
            region_name=self.region if self.region else None
        )

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Return AWS service name for boto3 client"""
        pass

    @abstractmethod
    def audit(self) -> List[Dict[str, Any]]:
        """Perform audit of the service and return results"""
        pass

    def handle_client_error(self, e: ClientError, resource: str) -> Dict[str, str]:
        """Handle and format AWS client errors"""
        return {
            'service': self.service_name,
            'resource': resource,
            'error': str(e),
            'region': self.region
        }