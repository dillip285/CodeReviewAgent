"""
Tests for the Bedrock service.
"""
import pytest
from unittest.mock import patch, MagicMock
from worker.bedrock_service import BedrockService

def test_construct_prompt_claude():
    """Test constructing a prompt for Claude."""
    # Create a Bedrock service
    bedrock_service = BedrockService(
        region="us-west-2",
        primary_model_id="anthropic.claude-instant-v1",
        fallback_model_id="amazon.titan-text-lite-v1",
    )
    
    # Create a test diff
    diff = "--- a/test.py\n+++ b/test.py\n@@ -1,3 +1,4 @@\n def hello():\n-    print(\"Hello, world!\")\n+    # This is a comment\n+    print(\"Hello, world!\")\n+    return None"
    
    # Create test Jira info
    jira_info = {
        "key": "TEST-123",
        "summary": "Test ticket",
        "description": "This is a test ticket",
        "status": "In Progress",
        "issue_type": "Task",
        "priority": "Medium",
        "epic": {
            "key": "EPIC-456",
            "summary": "Test epic",
        },
    }
    
    # Create test linter results
    linter_results = {
        "python": {
            "language": "python",
            "issues": [
                {
                    "file": "test.py",
                    "line": 3,
                    "column": 5,
                    "message": "Use a logger instead of print",
                    "severity": "warning",
                    "source": "pylint",
                },
            ],
        },
    }
    
    # Construct the prompt
    prompt = bedrock_service._construct_prompt(diff, jira_info, linter_results)
    
    # Check that the prompt contains the expected elements
    assert "<human>" in prompt
    assert "<system>" in prompt
    assert diff in prompt
    assert jira_info["key"] in prompt
    assert jira_info["summary"] in prompt
    assert jira_info["epic"]["key"] in prompt
    assert linter_results["python"]["issues"][0]["message"] in prompt

def test_construct_prompt_titan():
    """Test constructing a prompt for Titan."""
    # Create a Bedrock service
    bedrock_service = BedrockService(
        region="us-west-2",
        primary_model_id="amazon.titan-text-lite-v1",
        fallback_model_id="amazon.titan-text-lite-v1",
    )
    
    # Create a test diff
    diff = "--- a/test.py\n+++ b/test.py\n@@ -1,3 +1,4 @@\n def hello():\n-    print(\"Hello, world!\")\n+    # This is a comment\n+    print(\"Hello, world!\")\n+    return None"
    
    # Construct the prompt
    prompt = bedrock_service._construct_prompt(diff)
    
    # Check that the prompt contains the expected elements
    assert "System:" in prompt
    assert "Human:" in prompt
    assert "Assistant:" in prompt
    assert diff in prompt

@patch("boto3.client")
def test_invoke_model_claude(mock_boto3_client):
    """Test invoking a Claude model."""
    # Create a mock response
    mock_response = {
        "body": MagicMock(),
    }
    mock_response["body"].read.return_value = '{"completion": "This is a test response"}'
    
    # Configure the mock client
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = mock_response
    mock_boto3_client.return_value = mock_client
    
    # Create a Bedrock service
    bedrock_service = BedrockService(
        region="us-west-2",
        primary_model_id="anthropic.claude-instant-v1",
        fallback_model_id="amazon.titan-text-lite-v1",
    )
    
    # Invoke the model
    response = bedrock_service._invoke_model("anthropic.claude-instant-v1", "This is a test prompt")
    
    # Check the result
    assert response == "This is a test response"
    
    # Check that the client was called with the correct arguments
    mock_client.invoke_model.assert_called_once()
    args, kwargs = mock_client.invoke_model.call_args
    assert kwargs["modelId"] == "anthropic.claude-instant-v1"
    
    # Check that the request body contains the expected elements
    request_body = json.loads(kwargs["body"])
    assert "prompt" in request_body
    assert "max_tokens_to_sample" in request_body
    assert "temperature" in request_body

@patch("boto3.client")
def test_invoke_model_titan(mock_boto3_client):
    """Test invoking a Titan model."""
    # Create a mock response
    mock_response = {
        "body": MagicMock(),
    }
    mock_response["body"].read.return_value = '{"results": [{"outputText": "This is a test response"}]}'
    
    # Configure the mock client
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = mock_response
    mock_boto3_client.return_value = mock_client
    
    # Create a Bedrock service
    bedrock_service = BedrockService(
        region="us-west-2",
        primary_model_id="anthropic.claude-instant-v1",
        fallback_model_id="amazon.titan-text-lite-v1",
    )
    
    # Invoke the model
    response = bedrock_service._invoke_model("amazon.titan-text-lite-v1", "This is a test prompt")
    
    # Check the result
    assert response == "This is a test response"
    
    # Check that the client was called with the correct arguments
    mock_client.invoke_model.assert_called_once()
    args, kwargs = mock_client.invoke_model.call_args
    assert kwargs["modelId"] == "amazon.titan-text-lite-v1"
    
    # Check that the request body contains the expected elements
    request_body = json.loads(kwargs["body"])
    assert "inputText" in request_body
    assert "textGenerationConfig" in request_body