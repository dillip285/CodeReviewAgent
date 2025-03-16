"""
AWS SQS utilities for the Code Review Agent.
"""
import json
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

def get_sqs_client():
    """
    Get an AWS SQS client.
    
    Returns:
        An AWS SQS client
    """
    return boto3.client(
        "sqs",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

def send_message_to_sqs(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a message to the SQS queue.
    
    Args:
        message: The message to send
        
    Returns:
        The SQS response
    """
    try:
        client = get_sqs_client()
        response = client.send_message(
            QueueUrl=settings.SQS_QUEUE_URL,
            MessageBody=json.dumps(message),
            MessageAttributes={
                "MessageType": {
                    "DataType": "String",
                    "StringValue": "CodeReviewRequest",
                },
            },
        )
        return response
    except ClientError as e:
        logger.exception(f"Error sending message to SQS: {str(e)}")
        raise

def receive_messages_from_sqs(max_messages: int = 10, wait_time: int = 20) -> list:
    """
    Receive messages from the SQS queue.
    
    Args:
        max_messages: Maximum number of messages to receive
        wait_time: Wait time in seconds for long polling
        
    Returns:
        A list of messages
    """
    try:
        client = get_sqs_client()
        response = client.receive_message(
            QueueUrl=settings.SQS_QUEUE_URL,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time,
            MessageAttributeNames=["All"],
            AttributeNames=["All"],
        )
        return response.get("Messages", [])
    except ClientError as e:
        logger.exception(f"Error receiving messages from SQS: {str(e)}")
        raise

def delete_message_from_sqs(receipt_handle: str) -> Dict[str, Any]:
    """
    Delete a message from the SQS queue.
    
    Args:
        receipt_handle: The receipt handle of the message to delete
        
    Returns:
        The SQS response
    """
    try:
        client = get_sqs_client()
        response = client.delete_message(
            QueueUrl=settings.SQS_QUEUE_URL,
            ReceiptHandle=receipt_handle,
        )
        return response
    except ClientError as e:
        logger.exception(f"Error deleting message from SQS: {str(e)}")
        raise