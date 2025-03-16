"""
Celery application for the Code Review Agent.
"""
from celery import Celery

# Create the Celery application
app = Celery("code_review_agent")

# Load configuration from the celeryconfig.py module
app.config_from_object("app.celeryconfig")

if __name__ == "__main__":
    app.start()