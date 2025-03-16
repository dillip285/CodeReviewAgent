"""
Celery configuration for the Code Review Agent.
"""
from app.config import settings

# Broker settings
broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND

# Task settings
task_serializer = "json"
accept_content = ["json"]
result_serializer = "json"
timezone = "UTC"
enable_utc = True

# Task execution settings
task_acks_late = True
worker_prefetch_multiplier = 1
task_reject_on_worker_lost = True

# Task time limits
task_time_limit = 600  # 10 minutes
task_soft_time_limit = 540  # 9 minutes

# Retry settings
task_default_retry_delay = settings.RETRY_DELAY
task_max_retries = settings.MAX_RETRIES

# Logging
worker_hijack_root_logger = False
worker_log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Concurrency
worker_concurrency = 4  # Adjust based on your needs

# Task routes
task_routes = {
    "app.tasks.process_pull_request": {"queue": "code_review"},
}

# Task queues
task_queues = {
    "code_review": {
        "exchange": "code_review",
        "routing_key": "code_review",
    },
}