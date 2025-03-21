from typing import Dict, List, Any
from .base import AWSService
from botocore.exceptions import EndpointConnectionError, ClientError

class BedrockService(AWSService):
    def __init__(self, session, region=None):
        super().__init__(session, region)
        self.client = session.client('bedrock', region_name=region)

    @property
    def service_name(self) -> str:
        return 'bedrock'

    def audit(self) -> List[Dict[str, Any]]:
        try:
            models = self.client.list_foundation_models()
            return [self._get_model_details(model) for model in models['modelSummaries'] 
                   if self._get_model_details(model)]
        except (EndpointConnectionError, ClientError):
            # Service not available in this region
            return []
        except Exception as e:
            print(f"Unexpected error in Bedrock audit: {str(e)}")
            return []

    def _get_model_details(self, model: Dict[str, Any]) -> Dict[str, Any]:
        try:
            model_details = self.client.get_foundation_model(modelIdentifier=model['modelId'])
            return {
                'Region': self.region,
                'Model ID': model['modelId'],
                'Model Name': model['modelName'],
                'Provider': model['providerName'],
                'Status': model.get('modelLifecycle', {}).get('status', 'N/A'),
                'Input Modalities': ', '.join(model.get('inputModalities', [])),
                'Output Modalities': ', '.join(model.get('outputModalities', [])),
                'Custom Model': model.get('customizationsSupported', False),
                'Fine Tuning Supported': model.get('customModelSupported', False),
                'Response Streaming': model.get('responseStreamingSupported', False),
                'Model ARN': model.get('modelArn', 'N/A'),
                'Created At': str(model.get('createdAt', 'N/A')),
                'Last Modified': str(model.get('lastModifiedAt', 'N/A'))
            }
        except Exception:
            return None