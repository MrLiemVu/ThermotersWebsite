import firebase_functions as functions
from firebase_admin import initialize_app

# Initialize Firebase Admin SDK
app = initialize_app()

# Import and expose your functions
from .main import ping, submit_job, create_user_document

__all__ = ["ping", "submit_job", "create_user_document"] 