"""
AWS Bedrock service for the Code Review Agent worker.
"""
import json
import logging
from typing import Optional, Dict, Any, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BedrockService:
    """Service for interacting with AWS Bedrock."""
    
    def __init__(self, region: str, primary_model_id: str, fallback_model_id: str):
        """
        Initialize the Bedrock service.
        
        Args:
            region: The AWS region
            primary_model_id: The primary Bedrock model ID (e.g., anthropic.claude-instant-v1)
            fallback_model_id: The fallback Bedrock model ID (e.g., amazon.titan-text-lite-v1)
        """
        self.region = region
        self.primary_model_id = primary_model_id
        self.fallback_model_id = fallback_model_id
        self.client = boto3.client("bedrock-runtime", region_name=region)
    
    def generate_review(
        self,
        diff: str,
        jira_info: Optional[Dict[str, Any]] = None,
        linter_results: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Generate a code review using AWS Bedrock.
        
        Args:
            diff: The code diff
            jira_info: Optional Jira ticket information
            linter_results: Optional linter results
            
        Returns:
            The generated code review as a string, or None if an error occurred
        """
        try:
            # Construct the prompt
            prompt = self._construct_prompt(diff, jira_info, linter_results)
            
            # Try the primary model first
            response = self._invoke_model(self.primary_model_id, prompt)
            
            if not response:
                logger.warning(f"Primary model {self.primary_model_id} failed, trying fallback model")
                response = self._invoke_model(self.fallback_model_id, prompt)
            
            if not response:
                logger.error("Both primary and fallback models failed")
                return None
            
            return response
        
        except Exception as e:
            logger.exception(f"Error generating review: {str(e)}")
            return None
    
    def _construct_prompt(
        self,
        diff: str,
        jira_info: Optional[Dict[str, Any]] = None,
        linter_results: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Construct a prompt for the Bedrock model.
        
        Args:
            diff: The code diff
            jira_info: Optional Jira ticket information
            linter_results: Optional linter results
            
        Returns:
            The constructed prompt
        """
        # System prompt
        system_prompt = """
You are an expert code reviewer with deep knowledge of software engineering best practices, design patterns, and security considerations. Your task is to review a code diff and provide constructive feedback.

Your review should focus on:
1. Potential bugs or logic errors
2. Security vulnerabilities
3. Performance issues
4. Code style and readability
5. Design and architecture concerns
6. Maintainability and testability
7. Suggestions for improvement

Format your response as a Markdown document with the following sections:
- **Summary**: A brief overview of the changes and your overall assessment
- **Key Findings**: The most important issues that need to be addressed
- **Detailed Review**: A file-by-file breakdown of specific issues and suggestions
- **Recommendations**: Concrete steps to improve the code

Be specific in your feedback, referencing line numbers and code snippets where appropriate. Provide explanations for why certain patterns or practices are problematic and suggest alternatives.

Your tone should be professional, constructive, and helpful. Focus on the code, not the developer. Highlight both positive aspects and areas for improvement.
"""

        # Human prompt
        human_prompt = f"Please review the following code diff:\n\n```diff\n{diff}\n```\n\n"
        
        # Add Jira information if available
        if jira_info:
            human_prompt += f"""
## Jira Ticket Information
- **Key**: {jira_info.get('key', 'N/A')}
- **Summary**: {jira_info.get('summary', 'N/A')}
- **Description**: {jira_info.get('description', 'N/A')}
- **Status**: {jira_info.get('status', 'N/A')}
- **Type**: {jira_info.get('issue_type', 'N/A')}
- **Priority**: {jira_info.get('priority', 'N/A')}

"""
            
            # Add epic information if available
            if jira_info.get('epic'):
                human_prompt += f"""
## Epic Information
- **Key**: {jira_info['epic'].get('key', 'N/A')}
- **Summary**: {jira_info['epic'].get('summary', 'N/A')}

"""
        
        # Add linter results if available
        if linter_results:
            human_prompt += "## Linter Results\n\n"
            
            for language, results in linter_results.items():
                human_prompt += f"### {language} Linter Results\n\n"
                
                if not results.get('issues'):
                    human_prompt += "No issues found.\n\n"
                else:
                    for issue in results.get('issues', []):
                        human_prompt += f"- **{issue.get('severity', 'Issue')}**: {issue.get('message', 'N/A')} (File: {issue.get('file', 'N/A')}, Line: {issue.get('line', 'N/A')})\n"
                
                human_prompt += "\n"
        
        human_prompt += """
Please provide a comprehensive code review based on the diff and any additional information provided. Focus on identifying potential issues, suggesting improvements, and providing constructive feedback.
"""
        
        # Combine the prompts based on the model
        if self.primary_model_id.startswith("anthropic.claude"):
            # Claude prompt format
            prompt = f"<human>\n{human_prompt}\n</human>\n\n<system>\n{system_prompt}\n</system>"
        else:
            # Generic prompt format for other models
            prompt = f"System: {system_prompt}\n\nHuman: {human_prompt}\n\nAssistant:"
        
        return prompt
    
    def _invoke_model(self, model_id: str, prompt: str) -> Optional[str]:
        """
        Invoke a Bedrock model.
        
        Args:
            model_id: The Bedrock model ID
            prompt: The prompt to send to the model
            
        Returns:
            The model response as a string, or None if an error occurred
        """
        try:
            # Prepare the request body based on the model
            if model_id.startswith("anthropic.claude"):
                # Claude models
                request_body = {
                    "prompt": prompt,
                    "max_tokens_to_sample": 4096,
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "top_k": 250,
                    "stop_sequences": ["Human:", "<human>"]
                }
            elif model_id.startswith("amazon.titan"):
                # Titan models
                request_body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 4096,
                        "temperature": 0.2,
                        "topP": 0.9,
                        "stopSequences": []
                    }
                }
            else:
                logger.error(f"Unsupported model ID: {model_id}")
                return None
            
            # Invoke the model
            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response based on the model
            response_body = json.loads(response.get("body").read())
            
            if model_id.startswith("anthropic.claude"):
                # Claude models
                return response_body.get("completion")
            elif model_id.startswith("amazon.titan"):
                # Titan models
                return response_body.get("results")[0].get("outputText")
            else:
                logger.error(f"Unsupported model ID: {model_id}")
                return None
        
        except ClientError as e:
            logger.exception(f"Error invoking Bedrock model {model_id}: {str(e)}")
            return None