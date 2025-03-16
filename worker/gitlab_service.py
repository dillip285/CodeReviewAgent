"""
GitLab service for the Code Review Agent worker.
"""
import logging
from typing import Optional, Dict, Any, List
import gitlab
from gitlab.exceptions import GitlabError

logger = logging.getLogger(__name__)

class GitLabService:
    """Service for interacting with the GitLab API."""
    
    def __init__(self, url: str, token: str):
        """
        Initialize the GitLab service.
        
        Args:
            url: The GitLab instance URL
            token: The GitLab API token
        """
        self.url = url
        self.token = token
        self.client = gitlab.Gitlab(url=url, private_token=token)
    
    def get_project(self, project_id: int):
        """
        Get a GitLab project.
        
        Args:
            project_id: The project ID
            
        Returns:
            The GitLab project object
        """
        try:
            return self.client.projects.get(project_id)
        except GitlabError as e:
            logger.exception(f"Error getting project {project_id}: {str(e)}")
            return None
    
    def get_merge_request(self, project_id: int, merge_request_iid: int):
        """
        Get a GitLab merge request.
        
        Args:
            project_id: The project ID
            merge_request_iid: The merge request IID
            
        Returns:
            The GitLab merge request object
        """
        try:
            project = self.get_project(project_id)
            if not project:
                return None
            
            return project.mergerequests.get(merge_request_iid)
        except GitlabError as e:
            logger.exception(f"Error getting merge request {project_id}/{merge_request_iid}: {str(e)}")
            return None
    
    def get_merge_request_diff(self, project_id: int, merge_request_iid: int) -> Optional[str]:
        """
        Get the diff for a GitLab merge request.
        
        Args:
            project_id: The project ID
            merge_request_iid: The merge request IID
            
        Returns:
            The merge request diff as a string, or None if an error occurred
        """
        try:
            merge_request = self.get_merge_request(project_id, merge_request_iid)
            if not merge_request:
                return None
            
            # Get the changes
            changes = merge_request.changes()
            
            # Construct a unified diff
            diff_lines = []
            
            for change in changes.get("changes", []):
                old_path = change.get("old_path", "")
                new_path = change.get("new_path", "")
                diff = change.get("diff", "")
                
                # Add file header
                if old_path == new_path:
                    diff_lines.append(f"--- a/{old_path}")
                    diff_lines.append(f"+++ b/{new_path}")
                else:
                    diff_lines.append(f"--- a/{old_path}")
                    diff_lines.append(f"+++ b/{new_path}")
                
                # Add the diff
                diff_lines.append(diff)
            
            return "\n".join(diff_lines)
        
        except GitlabError as e:
            logger.exception(f"Error getting merge request diff {project_id}/{merge_request_iid}: {str(e)}")
            return None
    
    def post_comment(self, project_id: int, merge_request_iid: int, comment: str) -> bool:
        """
        Post a comment on a GitLab merge request.
        
        Args:
            project_id: The project ID
            merge_request_iid: The merge request IID
            comment: The comment text
            
        Returns:
            True if the comment was posted successfully, False otherwise
        """
        try:
            merge_request = self.get_merge_request(project_id, merge_request_iid)
            if not merge_request:
                return False
            
            # Post the comment
            merge_request.notes.create({"body": comment})
            
            logger.info(f"Posted comment on merge request {project_id}/{merge_request_iid}")
            return True
        
        except GitlabError as e:
            logger.exception(f"Error posting comment on merge request {project_id}/{merge_request_iid}: {str(e)}")
            return False
    
    def get_file_content(self, project_id: int, file_path: str, ref: str) -> Optional[str]:
        """
        Get the content of a file from a GitLab repository.
        
        Args:
            project_id: The project ID
            file_path: The file path
            ref: The branch or commit reference
            
        Returns:
            The file content as a string, or None if an error occurred
        """
        try:
            project = self.get_project(project_id)
            if not project:
                return None
            
            file = project.files.get(file_path=file_path, ref=ref)
            return file.decode().decode("utf-8")
        
        except GitlabError as e:
            logger.exception(f"Error getting file content {project_id}/{file_path}@{ref}: {str(e)}")
            return None