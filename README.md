# Code Review Agent

A comprehensive automated code review system that integrates with GitLab, Jira, and AWS Bedrock to provide intelligent feedback on pull requests.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Worker Service](#worker-service)
- [Linter Integration](#linter-integration)
- [AWS Bedrock Integration](#aws-bedrock-integration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Extending the Project](#extending-the-project)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Code Review Agent automatically reviews code changes submitted as GitLab pull requests. It leverages AWS Bedrock models (primarily Claude Instant, with fallback to Titan Text Lite) to analyze code diffs, identify potential issues, and provide constructive feedback. The agent also integrates with Jira to gather context from associated tickets and incorporates language-specific linter results to enhance the quality of reviews.

The system is designed to handle approximately 100 pull requests per hour and supports multiple programming languages including Python, Java, JavaScript, TypeScript, Go, and C#.

## Architecture

The Code Review Agent consists of several components:

1. **FastAPI Application**: Receives GitLab webhooks and queues review tasks.
2. **Celery Workers**: Process webhook payloads and send messages to SQS.
3. **SQS Queue**: Stores review requests for processing.
4. **Kubernetes Worker Pods**: Consume messages from SQS, fetch code diffs, run linters, generate reviews using AWS Bedrock, and post comments on GitLab pull requests.
5. **Redis**: Used as a broker and result backend for Celery.

![Architecture Diagram](https://mermaid.ink/img/pako:eNqNk01v2zAMhv8K4UuBFUjsJE2TQ4Fh2GXYpdiAYRd1B9qiHSGyZEhyGgzLf9_sOE3TDtiOEkU-fPmSvKCCVlCBLnXbcYNPTjvTcOtQfzFGO_LcGe3QkjNdTY_kLTpHjZEOtbHUcNvpGh_JGVNjTZZrNKRr7Yx2VJMzxhFZbY3GFp3TDWpyFjXVxDXXpA1qrLnWDVZkqUVHNbdIFTdYkW5Ro6OWO9LcQkXWoKMNd1CRMdxSxbXhDVRkW-0cNxUZbVqo6Gw2m0JFTc0bqMjVuqFHbqGiVnNHG9RQkdW8xQdUUJHmDVS0Qe2gIqOdhYpabqjlDVRkuSXDHVRkuKWKjDZQkdWmxQduoCLXcUsVOW0bqKjVriVHDVRkuYOKWu46qMho10BFG9M5rrGBilrToYWKjDYOKnLcQUWt5g1U5LRxUJHVvIGKnDYWKmq1a6Eip7mFijbcQUVbbrGBijpuqSLHbQsVOW5bqMhyBxVtuIOKWm6hIqONhYq23EFFRpsGKnLcQkUbbqGiDXdQkdXGQkVOGwcVOW4aqMhp00JFG-6gIqtdAxVtuYOKnDYtVGS5hYqcNi1UtOUOKnLcQkVOmxYqcto0UJHlDipqtWuhIqtdCxVZ7aBCeIGvMBcLWMJyAYvlYrGcw3wOy_liOYf5Yg6L5WK1gPkc5qvlar6E-RLmy-VqvoLlCuar1Wq-huUalqv1ar6B5QaWq_VqvoXlFpar9Wq-g-UOlqv1ar6H5R6Wq_Vqfj_8_wHzw-HwE-aHw-En_Dj8-A7zw-HwHX4efv6A-eFw-AE_Dz9_wfxwOPyC34ffv2F-OBx-w5_Dn78wPxwOf-Hv4e8_mB8Oh3_w7_DvP8wPh8N_-P_4H1OKRjA?type=png)

## Features

- **GitLab Integration**: Automatically processes merge request webhooks.
- **Jira Integration**: Extracts context from associated Jira tickets.
- **AWS Bedrock Integration**: Leverages Claude Instant and Titan Text Lite models for intelligent code review.
- **Multi-language Support**: Reviews code in Python, Java, JavaScript, TypeScript, Go, and C#.
- **Linter Integration**: Incorporates language-specific linter results.
- **Scalable Architecture**: Designed to handle high volumes of pull requests.
- **Fault Tolerance**: Includes retry mechanisms and dead-letter queues.
- **Kubernetes Deployment**: Runs on EKS with autoscaling capabilities.

## Project Structure

```
CodeReviewAgent/
├── app/                      # FastAPI application
│   ├── __init__.py
│   ├── main.py               # Main FastAPI application
│   ├── config.py             # Configuration settings
│   ├── celery_app.py         # Celery application
│   ├── celeryconfig.py       # Celery configuration
│   ├── tasks.py              # Celery tasks
│   └── utils/                # Utility functions
│       ├── __init__.py
│       ├── validators.py     # Webhook validation
│       └── sqs.py            # SQS integration
├── worker/                   # Kubernetes worker
│   ├── __init__.py
│   ├── main.py               # Main worker application
│   ├── Dockerfile            # Worker Dockerfile
│   ├── gitlab_service.py     # GitLab API integration
│   ├── jira_service.py       # Jira API integration
│   ├── bedrock_service.py    # AWS Bedrock integration
│   └── linter_service.py     # Language-specific linters
├── tests/                    # Unit tests
│   ├── __init__.py
│   ├── test_validators.py
│   ├── test_linter_service.py
│   └── test_bedrock_service.py
├── infrastructure/           # Infrastructure as code
│   ├── kubernetes/           # Kubernetes manifests
│   │   ├── api-deployment.yaml
│   │   ├── worker-deployment.yaml
│   │   ├── worker-hpa.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── config.yaml
│   │   └── ingress.yaml
│   └── sqs.yaml              # CloudFormation template for SQS
├── Dockerfile                # API Dockerfile
├── requirements.txt          # Python dependencies
├── .env.example              # Example environment variables
├── DEPLOYMENT.md             # Deployment instructions
└── README.md                 # This file
```

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- AWS account with access to:
  - AWS Bedrock
  - SQS
  - ECR
  - EKS
  - Secrets Manager
- GitLab account with API access
- Jira account with API access

## Local Development Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/code-review-agent.git
cd code-review-agent
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

5. Edit the `.env` file with your configuration settings.

6. Start Redis (required for Celery):

```bash
docker run -d -p 6379:6379 redis:7.0-alpine
```

7. Start the FastAPI application:

```bash
uvicorn app.main:app --reload
```

8. Start the Celery worker:

```bash
celery -A app.celery_app worker --loglevel=info
```

9. Start the SQS worker (for local development):

```bash
python worker/main.py
```

## Configuration

The application is configured using environment variables, which can be set in a `.env` file for local development or in Kubernetes ConfigMaps and Secrets for production.

### Required Configuration

```
# GitLab Configuration
GITLAB_URL=https://gitlab.example.com
GITLAB_API_TOKEN=your_gitlab_api_token
GITLAB_WEBHOOK_TOKEN=your_gitlab_webhook_token

# Jira Configuration
JIRA_URL=https://jira.example.com
JIRA_USERNAME=your_jira_username
JIRA_API_TOKEN=your_jira_api_token

# AWS Configuration
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

# AWS Bedrock Configuration
BEDROCK_MODEL_ID_PRIMARY=anthropic.claude-instant-v1
BEDROCK_MODEL_ID_FALLBACK=amazon.titan-text-lite-v1

# AWS SQS Configuration
SQS_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/123456789012/code-review-queue

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Optional Configuration

```
# Application Configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
MAX_RETRIES=3   # Maximum number of retries for failed tasks
RETRY_DELAY=5   # Delay between retries in seconds
MAX_DIFF_SIZE=100000  # Maximum diff size in bytes

# AWS Secrets Manager Configuration
USE_SECRETS_MANAGER=False  # Whether to use AWS Secrets Manager
SECRETS_NAME=code-review-secrets  # AWS Secrets Manager secret name
```

## API Endpoints

### `/health`

- **Method**: GET
- **Description**: Health check endpoint
- **Response**: `{"status": "healthy"}`

### `/review`

- **Method**: POST
- **Description**: Endpoint to receive GitLab webhook payloads for merge requests
- **Headers**:
  - `X-Gitlab-Token`: GitLab webhook token (for validation)
- **Request Body**: GitLab webhook payload
- **Response**: 
  - `202 Accepted`: `{"message": "Code review initiated for merge request {project_id}/{merge_request_iid}"}`
  - `400 Bad Request`: Invalid request
  - `500 Internal Server Error`: Server error

## Worker Service

The worker service is responsible for:

1. Consuming messages from SQS
2. Fetching code diffs from GitLab
3. Extracting Jira ticket information
4. Running language-specific linters
5. Generating code reviews using AWS Bedrock
6. Posting comments on GitLab merge requests

### Worker Flow

1. The worker polls the SQS queue for messages.
2. When a message is received, it extracts the project ID, merge request IID, and Jira ticket key.
3. It fetches the code diff from GitLab.
4. If a Jira ticket key is present, it fetches the ticket information.
5. It runs language-specific linters on the code.
6. It constructs a prompt for AWS Bedrock, including the code diff, Jira information, and linter results.
7. It sends the prompt to AWS Bedrock and receives a code review.
8. It posts the code review as a comment on the GitLab merge request.
9. It deletes the message from the SQS queue.

## Linter Integration

The Code Review Agent integrates with language-specific linters to provide static code analysis. The following linters are supported:

- **Python**: flake8, pylint
- **JavaScript**: ESLint
- **TypeScript**: ESLint with TypeScript plugin
- **Java**: Simple regex-based checks (can be extended with Checkstyle, PMD, or SpotBugs)
- **C#**: Simple regex-based checks (can be extended with StyleCop or FxCop)
- **Go**: go vet

### Adding a New Linter

To add a new linter:

1. Install the linter in the worker Dockerfile.
2. Add the file extension to the `supported_languages` dictionary in `LinterService.__init__`.
3. Implement a method to run the linter in `LinterService`.
4. Update the `run_linters` method to call your new linter method.

## AWS Bedrock Integration

The Code Review Agent uses AWS Bedrock to generate intelligent code reviews. It primarily uses Claude Instant, with fallback to Titan Text Lite if Claude is unavailable.

### Prompt Engineering

The prompt sent to AWS Bedrock includes:

1. A system prompt defining the agent's role and expectations.
2. The code diff.
3. Jira ticket information (if available).
4. Linter results.
5. Instructions for formatting the response as a Markdown report.

### Customizing the Prompt

To customize the prompt:

1. Modify the `_construct_prompt` method in `BedrockService`.
2. Adjust the system prompt to change the agent's personality or focus areas.
3. Modify the human prompt to include additional context or instructions.

### Using Different Models

To use different AWS Bedrock models:

1. Update the `BEDROCK_MODEL_ID_PRIMARY` and `BEDROCK_MODEL_ID_FALLBACK` environment variables.
2. If using a model with a different API format, update the `_invoke_model` method in `BedrockService`.

## Testing

The project includes unit tests for key components. To run the tests:

```bash
pytest
```

### Adding Tests

To add new tests:

1. Create a new test file in the `tests` directory.
2. Use pytest fixtures to mock dependencies.
3. Write test functions that assert expected behavior.

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Deployment Steps

1. Set up AWS infrastructure (EKS, SQS, ECR, Secrets Manager).
2. Build and push Docker images to ECR.
3. Update Kubernetes manifests with ECR repository URIs.
4. Deploy Kubernetes resources (ConfigMap, Secrets, Redis, API, Worker).
5. Configure GitLab webhook to point to the API endpoint.

## Extending the Project

### Adding Support for New Languages

To add support for a new programming language:

1. Add the file extension to the `supported_languages` dictionary in `LinterService.__init__`.
2. Implement a method to run linters for the new language in `LinterService`.
3. Update the `run_linters` method to call your new linter method.
4. Update the worker Dockerfile to install any necessary linters or dependencies.

### Adding New Features

Some ideas for extending the project:

1. **Code Quality Metrics**: Track code quality metrics over time.
2. **Custom Rules**: Allow teams to define custom rules for code reviews.
3. **User Feedback**: Allow users to provide feedback on code reviews.
4. **Integration with Other Code Hosting Platforms**: Add support for GitHub, Bitbucket, etc.
5. **Pre-commit Hooks**: Run code reviews before code is committed.
6. **Code Suggestions**: Automatically suggest fixes for common issues.
7. **Performance Analysis**: Analyze code for performance issues.
8. **Security Scanning**: Integrate with security scanning tools.

### Modifying the Code Review Format

To change the format of the code review:

1. Modify the system prompt in `BedrockService._construct_prompt`.
2. Update the `generate_review` method in `BedrockService` to parse the response differently if needed.
3. Modify the `post_comment` method in `GitLabService` to format the comment differently if needed.

## Troubleshooting

### Common Issues

#### Webhook Not Received

- Check that the GitLab webhook is correctly configured.
- Verify that the webhook token is correct.
- Check the API logs for any errors.

#### Worker Not Processing Messages

- Check that the worker is running and connected to SQS.
- Verify that the worker has the correct permissions to access SQS.
- Check the worker logs for any errors.

#### Bedrock API Errors

- Verify that the AWS credentials have permission to access Bedrock.
- Check that the Bedrock model IDs are correctly configured.
- Verify that the AWS region is correctly configured.

#### Linter Errors

- Check that the linters are correctly installed in the worker container.
- Verify that the linter configuration files are correctly set up.
- Check the worker logs for any linter-specific errors.

### Logging

The application uses Python's built-in logging module. The log level can be configured using the `LOG_LEVEL` environment variable.

To view logs:

- **API**: `kubectl logs -n code-review -l app=code-review-api`
- **Worker**: `kubectl logs -n code-review -l app=code-review-worker`

## Security Considerations

### API Security

- Use HTTPS for all API endpoints.
- Validate GitLab webhook tokens to prevent unauthorized access.
- Implement rate limiting to prevent abuse.

### Credential Management

- Store API tokens and credentials in AWS Secrets Manager.
- Use IAM roles with the principle of least privilege.
- Regularly rotate API tokens and credentials.

### Code Security

- Sanitize code diffs before processing to prevent injection attacks.
- Limit the size of code diffs to prevent resource exhaustion.
- Run linters in isolated environments to prevent code execution.

### Network Security

- Use Kubernetes network policies to restrict communication between pods.
- Use AWS security groups to restrict access to AWS resources.
- Implement VPC endpoints for AWS services to avoid public internet traffic.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Write tests for your changes.
5. Run the tests to ensure they pass.
6. Submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.