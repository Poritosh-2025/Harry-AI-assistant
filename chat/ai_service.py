"""
AI Service Client - Handles communication with external AI service.
Endpoint: 10.10.7.87:8015/chat
"""
import requests
import time
import logging
from django.conf import settings
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class AIServiceClient:
    """
    Client for communicating with the external AI chat service.
    Sends conversation history and receives AI responses.
    """
    
    def __init__(self):
        self.base_url = getattr(settings, 'AI_SERVICE_URL', 'https://harryai.dsrt321.online')
        self.chat_endpoint = f"{self.base_url}/chat"
        self.timeout = getattr(settings, 'AI_SERVICE_TIMEOUT', 60)  # 60 seconds default
        self.max_retries = getattr(settings, 'AI_SERVICE_MAX_RETRIES', 3)
    
    def send_message(
        self,
        conversation_history: List[Dict[str, str]],
        user_message: str
    ) -> Tuple[str, Dict]:
        """
        Send message to AI service with full conversation context.
        
        Args:
            conversation_history: List of previous messages [{'role': 'user/assistant', 'content': '...'}]
            user_message: Current user message
            
        Returns:
            Tuple of (ai_response_text, metadata_dict)
        """
        # Build the full conversation for context
        messages = conversation_history.copy()
        messages.append({
            'role': 'user',
            'content': user_message
        })
        
        # Prepare request payload
        payload = {
            'messages': messages,
            'message': user_message,  # Current message separately
            'conversation_history': conversation_history  # Previous context
        }
        
        metadata = {
            'tokens_used': None,
            'model_used': '',
            'response_time_ms': 0,
            'is_error': False,
            'error_message': ''
        }
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending request to AI service (attempt {attempt + 1})")
                
                response = requests.post(
                    self.chat_endpoint,
                    json=payload,
                    timeout=self.timeout,
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                )
                
                # Calculate response time
                metadata['response_time_ms'] = int((time.time() - start_time) * 1000)
                
                # Check response status
                response.raise_for_status()
                
                # Parse response
                response_data = response.json()
                
                # Extract AI response - handle different response formats
                ai_response = self._extract_response(response_data)
                
                # Extract metadata if available
                metadata['tokens_used'] = response_data.get('tokens_used') or response_data.get('usage', {}).get('total_tokens')
                metadata['model_used'] = response_data.get('model', '') or response_data.get('model_used', '')
                
                logger.info(f"AI service responded successfully in {metadata['response_time_ms']}ms")
                
                return ai_response, metadata
                
            except requests.exceptions.Timeout:
                logger.warning(f"AI service timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    metadata['is_error'] = True
                    metadata['error_message'] = 'AI service timeout. Please try again.'
                    metadata['response_time_ms'] = int((time.time() - start_time) * 1000)
                    return '', metadata
                    
            except requests.exceptions.ConnectionError:
                logger.error(f"AI service connection error (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    metadata['is_error'] = True
                    metadata['error_message'] = 'Unable to connect to AI service. Please try again later.'
                    metadata['response_time_ms'] = int((time.time() - start_time) * 1000)
                    return '', metadata
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"AI service HTTP error: {e}")
                metadata['is_error'] = True
                metadata['error_message'] = f'AI service error: {str(e)}'
                metadata['response_time_ms'] = int((time.time() - start_time) * 1000)
                return '', metadata
                
            except Exception as e:
                logger.error(f"Unexpected error calling AI service: {e}")
                metadata['is_error'] = True
                metadata['error_message'] = f'Unexpected error: {str(e)}'
                metadata['response_time_ms'] = int((time.time() - start_time) * 1000)
                return '', metadata
            
            # Wait before retry
            time.sleep(1 * (attempt + 1))
        
        return '', metadata
    
    def _extract_response(self, response_data: Dict) -> str:
        """
        Extract AI response from various response formats.
        Handles different API response structures.
        """
        # Try common response formats
        if isinstance(response_data, str):
            return response_data
        
        # Format: {'response': 'text'}
        if 'response' in response_data:
            return response_data['response']
        
        # Format: {'message': 'text'}
        if 'message' in response_data:
            return response_data['message']
        
        # Format: {'content': 'text'}
        if 'content' in response_data:
            return response_data['content']
        
        # Format: {'choices': [{'message': {'content': 'text'}}]} (OpenAI format)
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
            if 'text' in choice:
                return choice['text']
        
        # Format: {'data': {'response': 'text'}}
        if 'data' in response_data:
            data = response_data['data']
            if isinstance(data, str):
                return data
            if isinstance(data, dict):
                return data.get('response') or data.get('message') or data.get('content', '')
        
        # Format: {'result': 'text'}
        if 'result' in response_data:
            return response_data['result']
        
        # Format: {'answer': 'text'}
        if 'answer' in response_data:
            return response_data['answer']
        
        # Fallback: convert entire response to string
        logger.warning(f"Unknown AI response format: {response_data}")
        return str(response_data)
    
    def health_check(self) -> bool:
        """Check if AI service is available."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            # Try sending a simple message
            try:
                response = requests.post(
                    self.chat_endpoint,
                    json={'message': 'ping', 'messages': []},
                    timeout=10
                )
                return response.status_code in [200, 400]  # 400 might mean bad request but service is up
            except Exception:
                return False


# Singleton instance
ai_client = AIServiceClient()
