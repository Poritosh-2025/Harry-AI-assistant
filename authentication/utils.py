"""
Utility functions for authentication.
"""
import random
import string
import re
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def generate_otp(length=6):
    """Generate a random OTP code."""
    return ''.join(random.choices(string.digits, k=length))


def generate_reset_token():
    """Generate a random reset token."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=50))


def validate_password(password):
    """
    Validate password meets requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r'[@$!%*?&]', password):
        errors.append("Password must contain at least one special character (@$!%*?&).")
    
    return errors


def api_response(success, message, data=None, errors=None, status_code=status.HTTP_200_OK):
    """Generate standardized API response."""
    response_data = {
        'success': success,
        'message': message,
    }
    
    if data is not None:
        response_data['data'] = data
    
    if errors is not None:
        response_data['errors'] = errors
    
    return Response(response_data, status=status_code)


def custom_exception_handler(exc, context):
    """Custom exception handler for standardized error responses."""
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response = {
            'success': False,
            'message': 'An error occurred',
            'errors': {}
        }
        
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                custom_response['errors'] = exc.detail
                custom_response['message'] = 'Validation failed'
            elif isinstance(exc.detail, list):
                custom_response['errors'] = {'detail': exc.detail}
                custom_response['message'] = exc.detail[0] if exc.detail else 'An error occurred'
            else:
                custom_response['errors'] = {'detail': [str(exc.detail)]}
                custom_response['message'] = str(exc.detail)
        
        return Response(custom_response, status=response.status_code)
    
    return response
