"""
Tests for the validators module.
"""
import pytest
from fastapi import Request
from app.utils.validators import validate_gitlab_webhook
from app.config import settings

class MockRequest:
    """Mock Request class for testing."""
    
    def __init__(self, headers=None):
        """Initialize the mock request."""
        self.headers = headers or {}

def test_validate_gitlab_webhook_no_token():
    """Test validating a GitLab webhook with no token configured."""
    # Save the original token
    original_token = settings.GITLAB_WEBHOOK_TOKEN
    
    try:
        # Set the token to None
        settings.GITLAB_WEBHOOK_TOKEN = None
        
        # Create a mock request
        request = MockRequest()
        
        # Validate the webhook
        is_valid, error_msg = validate_gitlab_webhook(request, {})
        
        # Check the result
        assert is_valid
        assert error_msg == ""
    
    finally:
        # Restore the original token
        settings.GITLAB_WEBHOOK_TOKEN = original_token

def test_validate_gitlab_webhook_missing_header():
    """Test validating a GitLab webhook with a missing header."""
    # Save the original token
    original_token = settings.GITLAB_WEBHOOK_TOKEN
    
    try:
        # Set the token
        settings.GITLAB_WEBHOOK_TOKEN = "test_token"
        
        # Create a mock request with no headers
        request = MockRequest()
        
        # Validate the webhook
        is_valid, error_msg = validate_gitlab_webhook(request, {})
        
        # Check the result
        assert not is_valid
        assert error_msg == "Missing X-Gitlab-Token header"
    
    finally:
        # Restore the original token
        settings.GITLAB_WEBHOOK_TOKEN = original_token

def test_validate_gitlab_webhook_invalid_token():
    """Test validating a GitLab webhook with an invalid token."""
    # Save the original token
    original_token = settings.GITLAB_WEBHOOK_TOKEN
    
    try:
        # Set the token
        settings.GITLAB_WEBHOOK_TOKEN = "test_token"
        
        # Create a mock request with an invalid token
        request = MockRequest(headers={"X-Gitlab-Token": "invalid_token"})
        
        # Validate the webhook
        is_valid, error_msg = validate_gitlab_webhook(request, {})
        
        # Check the result
        assert not is_valid
        assert error_msg == "Invalid GitLab webhook token"
    
    finally:
        # Restore the original token
        settings.GITLAB_WEBHOOK_TOKEN = original_token

def test_validate_gitlab_webhook_valid_token():
    """Test validating a GitLab webhook with a valid token."""
    # Save the original token
    original_token = settings.GITLAB_WEBHOOK_TOKEN
    
    try:
        # Set the token
        settings.GITLAB_WEBHOOK_TOKEN = "test_token"
        
        # Create a mock request with a valid token
        request = MockRequest(headers={"X-Gitlab-Token": "test_token"})
        
        # Validate the webhook
        is_valid, error_msg = validate_gitlab_webhook(request, {})
        
        # Check the result
        assert is_valid
        assert error_msg == ""
    
    finally:
        # Restore the original token
        settings.GITLAB_WEBHOOK_TOKEN = original_token