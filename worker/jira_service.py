"""
Jira service for the Code Review Agent worker.
"""
import logging
from typing import Optional, Dict, Any, List
from jira import JIRA
from jira.exceptions import JIRAError

logger = logging.getLogger(__name__)

class JiraService:
    """Service for interacting with the Jira API."""
    
    def __init__(self, url: str, username: str, token: str):
        """
        Initialize the Jira service.
        
        Args:
            url: The Jira instance URL
            username: The Jira username
            token: The Jira API token
        """
        self.url = url
        self.username = username
        self.token = token
        self.client = JIRA(
            server=url,
            basic_auth=(username, token),
        )
    
    def get_ticket_info(self, ticket_key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a Jira ticket.
        
        Args:
            ticket_key: The Jira ticket key (e.g., PROJ-123)
            
        Returns:
            A dictionary containing ticket information, or None if an error occurred
        """
        try:
            issue = self.client.issue(ticket_key)
            
            # Extract basic issue information
            info = {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description or "",
                "status": issue.fields.status.name,
                "issue_type": issue.fields.issuetype.name,
                "priority": issue.fields.priority.name if hasattr(issue.fields, "priority") and issue.fields.priority else "Unassigned",
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "comments": [],
                "labels": issue.fields.labels,
                "components": [c.name for c in issue.fields.components],
                "epic": None,
            }
            
            # Extract comments
            if hasattr(issue.fields, "comment"):
                for comment in issue.fields.comment.comments:
                    info["comments"].append({
                        "author": comment.author.displayName,
                        "body": comment.body,
                        "created": comment.created,
                    })
            
            # Extract epic link if available
            if hasattr(issue.fields, "customfield_10014") and issue.fields.customfield_10014:
                epic_key = issue.fields.customfield_10014
                try:
                    epic = self.client.issue(epic_key)
                    info["epic"] = {
                        "key": epic.key,
                        "summary": epic.fields.summary,
                    }
                except JIRAError:
                    logger.warning(f"Failed to fetch epic {epic_key} for ticket {ticket_key}")
            
            return info
        
        except JIRAError as e:
            logger.exception(f"Error getting Jira ticket {ticket_key}: {str(e)}")
            return None