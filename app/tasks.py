"""
Celery tasks for the Code Review Agent.
"""
import logging
import json
from celery import shared_task
from app.celery_app import app
from app.config import settings
from app.utils.sqs import send_message_to_sqs

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    name="app.tasks.process_pull_request",
    max_retries=settings.MAX_RETRIES,
    default_retry_delay=settings.RETRY_DELAY,
)
def process_pull_request(
    self,
    project_id: int,
    merge_request_iid: int,
    source_branch: str,
    target_branch: str,
    description: str,
):
    """
    Process a GitLab merge request and send it to SQS for review.
    
    Args:
        project_id: The GitLab project ID
        merge_request_iid: The merge request IID
        source_branch: The source branch
        target_branch: The target branch
        description: The merge request description
    """
    try:
        logger.info(f"Processing merge request {project_id}/{merge_request_iid}")
        
        # Extract Jira ticket key from description (if present)
        jira_ticket_key = None
        import re
        jira_pattern = r'([A-Z]+-\d+)'
        match = re.search(jira_pattern, description)
        if match:
            jira_ticket_key = match.group(1)
            logger.info(f"Found Jira ticket key: {jira_ticket_key}")
        
        # Prepare message for SQS
        message = {
            "project_id": project_id,
            "merge_request_iid": merge_request_iid,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "jira_ticket_key": jira_ticket_key,
        }
        
        # Send message to SQS
        response = send_message_to_sqs(message)
        logger.info(f"Sent message to SQS: {response}")
        
        return {
            "status": "success",
            "message": f"Merge request {project_id}/{merge_request_iid} sent to SQS for review",
            "sqs_message_id": response.get("MessageId"),
        }
    
    except Exception as e:
        logger.exception(f"Error processing merge request: {str(e)}")
        # Retry the task
        self.retry(exc=e)