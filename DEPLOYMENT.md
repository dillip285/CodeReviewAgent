# Deployment Guide for Code Review Agent

This guide provides step-by-step instructions for deploying the Code Review Agent to AWS using Kubernetes (EKS).

## Prerequisites

- AWS CLI installed and configured with appropriate permissions
- kubectl installed
- eksctl installed
- Docker installed
- Access to an AWS account with permissions to create:
  - EKS clusters
  - ECR repositories
  - SQS queues
  - Secrets Manager secrets
  - IAM roles and policies

## Step 1: Set up AWS Infrastructure

### Create an EKS Cluster

```bash
eksctl create cluster \
  --name code-review-cluster \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed
```

### Create SQS Queues

Deploy the SQS CloudFormation template:

```bash
aws cloudformation deploy \
  --template-file infrastructure/sqs.yaml \
  --stack-name code-review-sqs \
  --region us-west-2
```

### Create ECR Repositories

```bash
aws ecr create-repository --repository-name code-review-api --region us-west-2
aws ecr create-repository --repository-name code-review-worker --region us-west-2
```

### Store Secrets in AWS Secrets Manager

```bash
aws secretsmanager create-secret \
  --name code-review-secrets \
  --description "Secrets for Code Review Agent" \
  --secret-string '{
    "GITLAB_URL": "https://gitlab.example.com",
    "GITLAB_API_TOKEN": "your_gitlab_api_token",
    "GITLAB_WEBHOOK_TOKEN": "your_gitlab_webhook_token",
    "JIRA_URL": "https://jira.example.com",
    "JIRA_USERNAME": "your_jira_username",
    "JIRA_API_TOKEN": "your_jira_api_token",
    "AWS_ACCESS_KEY_ID": "your_aws_access_key_id",
    "AWS_SECRET_ACCESS_KEY": "your_aws_secret_access_key"
  }' \
  --region us-west-2
```

## Step 2: Build and Push Docker Images

### Build and Push the API Image

```bash
# Get the ECR repository URI
API_REPO_URI=$(aws ecr describe-repositories --repository-names code-review-api --query 'repositories[0].repositoryUri' --output text --region us-west-2)

# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $API_REPO_URI

# Build and push the API image
docker build -t $API_REPO_URI:latest -f Dockerfile .
docker push $API_REPO_URI:latest
```

### Build and Push the Worker Image

```bash
# Get the ECR repository URI
WORKER_REPO_URI=$(aws ecr describe-repositories --repository-names code-review-worker --query 'repositories[0].repositoryUri' --output text --region us-west-2)

# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $WORKER_REPO_URI

# Build and push the worker image
docker build -t $WORKER_REPO_URI:latest -f worker/Dockerfile .
docker push $WORKER_REPO_URI:latest
```

## Step 3: Deploy to Kubernetes

### Update Kubernetes Manifests

Replace the placeholder `${ECR_REPOSITORY_URI}` in the Kubernetes manifests with the actual ECR repository URIs:

```bash
# Update the API deployment manifest
sed -i "s|\${ECR_REPOSITORY_URI}|$API_REPO_URI|g" infrastructure/kubernetes/api-deployment.yaml

# Update the worker deployment manifest
sed -i "s|\${ECR_REPOSITORY_URI}|$WORKER_REPO_URI|g" infrastructure/kubernetes/worker-deployment.yaml
```

### Create the Kubernetes Namespace and ConfigMap/Secrets

```bash
kubectl apply -f infrastructure/kubernetes/config.yaml
```

### Deploy Redis

```bash
kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml
```

### Deploy the API

```bash
kubectl apply -f infrastructure/kubernetes/api-deployment.yaml
```

### Deploy the Worker

```bash
kubectl apply -f infrastructure/kubernetes/worker-deployment.yaml
```

### Configure Horizontal Pod Autoscaler

```bash
kubectl apply -f infrastructure/kubernetes/worker-hpa.yaml
```

### Deploy the Ingress

```bash
# Install the AWS Load Balancer Controller
eksctl create iamserviceaccount \
  --cluster=code-review-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::123456789012:policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --approve

helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=code-review-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Deploy the ingress
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

## Step 4: Configure GitLab Webhook

1. Get the ALB URL:

```bash
kubectl get ingress code-review-ingress -n code-review -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

2. In GitLab, go to your project's settings > Webhooks.
3. Add a new webhook with the following settings:
   - URL: `http://<ALB_URL>/review`
   - Secret Token: The same token you stored in AWS Secrets Manager
   - Trigger: Merge request events
   - SSL verification: Enabled (if using HTTPS)
4. Click "Add webhook"

## Step 5: Verify the Deployment

### Check the API Deployment

```bash
kubectl get pods -n code-review -l app=code-review-api
```

### Check the Worker Deployment

```bash
kubectl get pods -n code-review -l app=code-review-worker
```

### Check the Redis Deployment

```bash
kubectl get pods -n code-review -l app=redis
```

### Check the Logs

```bash
# API logs
kubectl logs -n code-review -l app=code-review-api

# Worker logs
kubectl logs -n code-review -l app=code-review-worker
```

## Step 6: Test the Deployment

1. Create a new merge request in GitLab.
2. Check the logs to verify that the webhook was received and processed.
3. Verify that a comment was posted on the merge request with the code review.

## Troubleshooting

### Webhook Issues

- Check the API logs for any errors related to webhook validation.
- Verify that the GitLab webhook token is correctly configured.
- Check that the ALB is correctly routing traffic to the API service.

### Worker Issues

- Check the worker logs for any errors related to processing merge requests.
- Verify that the worker has access to the SQS queue.
- Check that the worker has access to the GitLab and Jira APIs.

### Bedrock Issues

- Verify that the AWS credentials have permission to access Bedrock.
- Check that the Bedrock model IDs are correctly configured.
- Verify that the AWS region is correctly configured.

## Maintenance

### Updating the Application

1. Make changes to the code.
2. Build and push new Docker images.
3. Update the Kubernetes deployments:

```bash
kubectl rollout restart deployment code-review-api -n code-review
kubectl rollout restart deployment code-review-worker -n code-review
```

### Scaling the Application

The worker deployment is configured with a Horizontal Pod Autoscaler that will automatically scale based on CPU and memory usage. You can manually scale the deployments if needed:

```bash
kubectl scale deployment code-review-worker -n code-review --replicas=5
```

### Monitoring

Set up CloudWatch monitoring for the EKS cluster, SQS queues, and Bedrock API calls to track usage and performance.

## Security Considerations

- Use IAM roles with the principle of least privilege.
- Regularly rotate API tokens and secrets.
- Enable encryption at rest for SQS queues and Secrets Manager secrets.
- Use network policies to restrict communication between pods.
- Implement rate limiting for the API to prevent abuse.
- Regularly update dependencies to address security vulnerabilities.