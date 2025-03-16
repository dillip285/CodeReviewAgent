"""
Configuration module for the Code Review Agent.

This module loads configuration from environment variables and AWS Secrets Manager.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # GitLab Configuration
    GITLAB_URL: str = Field(..., description="GitLab instance URL")
    GITLAB_API_TOKEN: str = Field(..., description="GitLab API token")
    GITLAB_WEBHOOK_TOKEN: Optional[str] = Field(None, description="GitLab webhook token for validation")
    
    # Jira Configuration
    JIRA_URL: str = Field(..., description="Jira instance URL")
    JIRA_USERNAME: str = Field(..., description="Jira username")
    JIRA_API_TOKEN: str = Field(..., description="Jira API token")
    
    # AWS Configuration
    AWS_REGION: str = Field("us-west-2", description="AWS region")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, description="AWS access key ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, description="AWS secret access key")
    
    # AWS Bedrock Configuration
    BEDROCK_MODEL_ID_PRIMARY: str = Field(
        "anthropic.claude-instant-v1", 
        description="Primary AWS Bedrock model ID"
    )
    BEDROCK_MODEL_ID_FALLBACK: str = Field(
        "amazon.titan-text-lite-v1", 
        description="Fallback AWS Bedrock model ID"
    )
    
    # AWS SQS Configuration
    SQS_QUEUE_URL: str = Field(..., description="AWS SQS queue URL")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = Field("redis://localhost:6379/0", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field("redis://localhost:6379/0", description="Celery result backend URL")
    
    # Application Configuration
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    MAX_RETRIES: int = Field(3, description="Maximum number of retries for failed tasks")
    RETRY_DELAY: int = Field(5, description="Delay between retries in seconds")
    MAX_DIFF_SIZE: int = Field(100000, description="Maximum diff size in bytes")
    
    # AWS Secrets Manager Configuration
    USE_SECRETS_MANAGER: bool = Field(False, description="Whether to use AWS Secrets Manager")
    SECRETS_NAME: Optional[str] = Field(None, description="AWS Secrets Manager secret name")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

def get_secrets() -> Dict[str, Any]:
    """
    Retrieve secrets from AWS Secrets Manager.
    
    Returns:
        A dictionary containing the secrets
    """
    if not settings.USE_SECRETS_MANAGER or not settings.SECRETS_NAME:
        return {}
    
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name="secretsmanager",
            region_name=settings.AWS_REGION,
        )
        response = client.get_secret_value(SecretId=settings.SECRETS_NAME)
        return json.loads(response["SecretString"])
    except ClientError as e:
        logger.error(f"Error retrieving secrets: {str(e)}")
        return {}

# Load settings from environment variables
settings = Settings()

# Load secrets from AWS Secrets Manager if enabled
if settings.USE_SECRETS_MANAGER:
    secrets = get_secrets()
    
    # Update settings with secrets
    for key, value in secrets.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)