"""
Main module for the Code Review Agent worker.

This worker consumes messages from SQS, processes them, and posts the results to GitLab.
"""
import json
import logging
import time
import sys
import os
import signal
from typing import Dict, Any, Optional

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.utils.sqs import receive_messages_from_sqs, delete_message_from_sqs
from worker.gitlab_service import GitLabService
from worker.jira_service import JiraService
from worker.bedrock_service import BedrockService
from worker.linter_service import LinterService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global flag to indicate if the worker should continue running
running = True

def signal_handler(sig, frame):
    """Handle signals to gracefully shut down the worker."""
    global running
    logger.info(f"Received signal {sig}, shutting down...")
    running = False

def process_message(message: Dict[str, Any]) -> bool:
    """
    Process a message from SQS.
    
    Args:
        message: The SQS message
        
    Returns:
        True if the message was processed successfully, False otherwise
    """
    try:
        # Parse the message body
        body = json.loads(message["Body"])
        logger.info(f"Processing message: {body}")
        
        # Extract message data
        project_id = body.get("project_id")
        merge_request_iid = body.get("merge_request_iid")
        jira_ticket_key = body.get("jira_ticket_key")
        
        if not project_id or not merge_request_iid:
            logger.error("Missing required fields in message")
            return False
        
        # Initialize services
        gitlab_service = GitLabService(
            url=settings.GITLAB_URL,
            token=settings.GITLAB_API_TOKEN,
        )
        
        # Fetch the merge request diff
        diff = gitlab_service.get_merge_request_diff(project_id, merge_request_iid)
        if not diff:
            logger.error(f"Failed to fetch diff for merge request {project_id}/{merge_request_iid}")
            return False
        
        # Check if the diff is too large
        if len(diff.encode("utf-8")) > settings.MAX_DIFF_SIZE:
            logger.warning(f"Diff for merge request {project_id}/{merge_request_iid} is too large")
            gitlab_service.post_comment(
                project_id,
                merge_request_iid,
                "⚠️ The diff for this merge request is too large for automated review. Please consider breaking it down into smaller changes.",
            )
            return True
        
        # Fetch Jira ticket information if available
        jira_info = None
        if jira_ticket_key:
            jira_service = JiraService(
                url=settings.JIRA_URL,
                username=settings.JIRA_USERNAME,
                token=settings.JIRA_API_TOKEN,
            )
            jira_info = jira_service.get_ticket_info(jira_ticket_key)
        
        # Run linters on the code
        linter_service = LinterService()
        linter_results = linter_service.run_linters(diff)
        
        # Generate the code review using AWS Bedrock
        bedrock_service = BedrockService(
            region=settings.AWS_REGION,
            primary_model_id=settings.BEDROCK_MODEL_ID_PRIMARY,
            fallback_model_id=settings.BEDROCK_MODEL_ID_FALLBACK,
        )
        
        review = bedrock_service.generate_review(
            diff=diff,
            jira_info=jira_info,
            linter_results=linter_results,
        )
        
        if not review:
            logger.error(f"Failed to generate review for merge request {project_id}/{merge_request_iid}")
            return False
        
        # Post the review as a comment on the merge request
        gitlab_service.post_comment(project_id, merge_request_iid, review)
        
        logger.info(f"Successfully processed merge request {project_id}/{merge_request_iid}")
        return True
    
    except Exception as e:
        logger.exception(f"Error processing message: {str(e)}")
        return False

def main():
    """Main entry point for the worker."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Code Review Agent worker")
    
    while running:
        try:
            # Receive messages from SQS
            messages = receive_messages_from_sqs()
            
            if not messages:
                logger.debug("No messages received, waiting...")
                time.sleep(5)
                continue
            
            logger.info(f"Received {len(messages)} messages")
            
            # Process each message
            for message in messages:
                receipt_handle = message.get("ReceiptHandle")
                
                if not receipt_handle:
                    logger.error("Message missing receipt handle")
                    continue
                
                # Process the message
                success = process_message(message)
                
                # Delete the message if it was processed successfully
                if success:
                    delete_message_from_sqs(receipt_handle)
                    logger.info(f"Deleted message {receipt_handle}")
        
        except Exception as e:
            logger.exception(f"Error in main loop: {str(e)}")
            time.sleep(5)
    
    logger.info("Worker shutting down")

if __name__ == "__main__":
    main()