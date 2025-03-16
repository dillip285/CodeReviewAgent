"""
Main FastAPI application for the Code Review Agent.
This module handles GitLab webhooks and initiates the code review process.
"""
import logging
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from app.config import settings
from app.tasks import process_pull_request
from app.utils.validators import validate_gitlab_webhook

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Code Review Agent",
    description="An automated code review agent for GitLab pull requests",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/review")
async def review_code(request: Request):
    """
    Endpoint to receive GitLab webhook payloads for merge requests.
    
    Args:
        request: The incoming HTTP request containing the GitLab webhook payload
        
    Returns:
        A JSON response indicating the status of the review request
    """
    try:
        # Get the raw request body
        body = await request.body()
        payload = json.loads(body)
        
        # Validate the GitLab webhook
        is_valid, error_msg = validate_gitlab_webhook(request, payload)
        if not is_valid:
            logger.error(f"Invalid GitLab webhook: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid GitLab webhook: {error_msg}",
            )
        
        # Check if this is a merge request event
        if payload.get("object_kind") != "merge_request":
            logger.info("Ignoring non-merge request event")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "Ignoring non-merge request event"},
            )
        
        # Check if this is an action we want to process
        valid_actions = ["open", "update", "reopen"]
        action = payload.get("object_attributes", {}).get("action")
        if action not in valid_actions:
            logger.info(f"Ignoring merge request action: {action}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": f"Ignoring merge request action: {action}"},
            )
        
        # Extract relevant information from the payload
        merge_request = payload.get("object_attributes", {})
        project_id = merge_request.get("target_project_id")
        merge_request_iid = merge_request.get("iid")
        source_branch = merge_request.get("source_branch")
        target_branch = merge_request.get("target_branch")
        description = merge_request.get("description", "")
        
        if not all([project_id, merge_request_iid, source_branch, target_branch]):
            logger.error("Missing required merge request information")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required merge request information",
            )
        
        # Send the task to Celery for processing
        logger.info(f"Processing merge request {project_id}/{merge_request_iid}")
        process_pull_request.delay(
            project_id=project_id,
            merge_request_iid=merge_request_iid,
            source_branch=source_branch,
            target_branch=target_branch,
            description=description,
        )
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"message": f"Code review initiated for merge request {project_id}/{merge_request_iid}"},
        )
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    except Exception as e:
        logger.exception(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}",
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Custom exception handler for general exceptions."""
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)