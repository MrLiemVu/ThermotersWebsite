from firebase_functions import https_fn
from firebase_admin import initialize_app, firestore
import firebase_admin
from firebase_admin import credentials
import os
import uuid

# Initialize Firebase
cred = credentials.ApplicationDefault()
initialize_app(cred, {
    'projectId': os.getenv('GCLOUD_PROJECT'),
    'storageBucket': 'thermoterswebsite.appspot.com'
})

db = firestore.client()

@https_fn.on_call()
def submit_job(req: https_fn.CallableRequest) -> dict:
    """Handles job submission from the client"""
    # Authentication check
    if not req.auth:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.FAILED_PRECONDITION,
            message="Authentication required"
        )

    # Input validation
    try:
        job_data = req.data
        sequence = str(job_data['sequence'])
        predictors = job_data['predictors']
        job_title = str(job_data['jobTitle'])
    except (KeyError, ValueError) as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="Invalid job data"
        )

    # Generate job ID
    job_id = str(uuid.uuid4())
    user_id = req.auth.uid

    try:
        # Save to Firestore
        doc_ref = db.collection('users').document(user_id).collection('jobs').document(job_id)
        doc_ref.set({
            'jobId': job_id,
            'userId': user_id,
            'sequence': sequence,
            'predictors': predictors,
            'jobTitle': job_title,
            'status': 'pending',
            'createdAt': firestore.SERVER_TIMESTAMP
        })

        return {'status': 'success', 'jobId': job_id}

    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Job submission failed: {str(e)}"
        )