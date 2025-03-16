"""
Validation utilities for the Code Review Agent.
"""
import hmac
import hashlib
from typing import Tuple
from fastapi import Request
from app.config import settings

def validate_gitlab_webhook(request: Request, payload: dict) -> Tuple[bool, str]:
    """
    Validate that the webhook request is from GitLab.
    
    Args:
        request: The incoming HTTP request
        payload: The parsed JSON payload
        
    Returns:
        A tuple containing (is_valid, error_message)
    """
    # In production, you should validate the GitLab webhook token
    # This is a simplified version for demonstration purposes
    
    # Check if the webhook token is configured
    if not settings.GITLAB_WEBHOOK_TOKEN:
        return True, ""  # Skip validation if token is not configured
    
    # Get the GitLab token from the request headers
    gitlab_token = request.headers.get("X-Gitlab-Token")
    
    if not gitlab_token:
        return False, "Missing X-Gitlab-Token header"
    
    # Validate the token
    if gitlab_token != settings.GITLAB_WEBHOOK_TOKEN:
        return False, "Invalid GitLab webhook token"
    
    return True, ""