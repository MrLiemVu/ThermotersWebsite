import os, re, datetime, uuid
from firebase_functions import https_fn, firestore_fn
from BrickPlotter import BrickPlotter
from datetime import datetime, timedelta
from google.cloud import storage
from dotenv import load_dotenv
from firebase_admin import firestore, credentials, initialize_app

load_dotenv()  # Load environment variables from .env file

# Validate environment variables
if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

cred_path = os.path.abspath(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
if not os.path.exists(cred_path):
    raise FileNotFoundError(f"Service account key file not found at {cred_path}")

# Initialize Firebase Admin
cred = credentials.Certificate(cred_path)
initialize_app(cred)

# Now safe to initialize Firestore
db = firestore.client()

JOB_STATUS = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed',
    'ERROR': 'error'
}

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
        model = str(job_data['model'])
        is_plus_one = bool(job_data['isPlusOne'])
        is_rc = bool(job_data['isRc'])
        max_value = float(job_data['maxValue'])
        min_value = float(job_data['minValue'])
        is_high_to_default = bool(job_data['isHighToDefault'])
        threshold = float(job_data['threshold'])
        is_prefix_suffix = bool(job_data['isPrefixSuffix'])
    except (KeyError, ValueError) as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=f"Invalid job data: {str(e)}"
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
            'createdAt': datetime.now()
        })

        # Generate brickplot
        brick_data = get_brickplot(
            model=model,
            sequence=sequence,
            is_plus_one=is_plus_one,
            is_rc=is_rc,
            max_value=max_value,
            min_value=min_value,
            is_high_to_default=is_high_to_default,
            threshold=threshold,
            is_prefix_suffix=is_prefix_suffix
        )
        
        return {
            'status': 'success', 
            'jobId': job_id,
            'image': f"data:image/png;base64,{brick_data['image_base64']}",
            'sequence': brick_data['sequence'],
            'plot_data': brick_data['plot_data']
        }

    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Job submission failed: {str(e)}"
        )

def get_brickplot(model, sequence, is_plus_one=True, 
                  is_rc=False, max_value=-2.5, min_value=-6, 
                  is_high_to_default=False, threshold=-2.5, is_prefix_suffix=True):
    output_folder = "brickplots"
    brickplotter = BrickPlotter(model=model,
                                output_folder=output_folder,
                                is_plus_one=is_plus_one,
                                is_rc=is_rc,
                                max_value=max_value,
                                min_value=min_value,
                                is_high_to_default=is_high_to_default,
                                threshold=threshold,
                                is_prefix_suffix=is_prefix_suffix
                                )
    brickplot = brickplotter.get_brickplot(sequence)
    return brickplot

@firestore_fn.on_document_created(document="users/{userId}/jobs/{jobId}")
def process_job(event: firestore_fn.Event) -> None:
    """Triggered when a new job is added to user's job history"""
    job_data = event.data.to_dict()
    job_id = event.params['jobId']
    user_id = event.params['userId']

    firestore_client = firestore.client()
    job_ref = firestore_client.document(f"users/{user_id}/jobs/{job_id}")

    try:
        # Update status to processing
        job_ref.update({
            'status': JOB_STATUS['PROCESSING'],
            'processingStartedAt': datetime.now()
        })

        # Process job data (replace with actual processing logic)
        processed_data = process_gene_data(job_data)

        # Update job with results
        job_ref.update({
            'status': JOB_STATUS['COMPLETED'],
            'results': processed_data,
            'completedAt': datetime.now()
        })

        # Update user's last job reference
        user_ref = firestore_client.document(f"users/{user_id}")
        user_ref.update({'lastJob': job_id})

    except Exception as e:
        job_ref.update({
            'status': JOB_STATUS['ERROR'],
            'error': str(e),
            'errorAt': datetime.now()
        })

def process_gene_data(job_data: dict) -> dict:
    """Process gene sequence data (example implementation)"""
    return {
        'brickplot': "Sample brickplot data",
        'predictors': job_data.get('predictors', []),
        'sequence': job_data.get('sequence', '')
    }

def create_user_document(event: firestore_fn.Event) -> None:
    """Triggered when a new user is created"""
    user_data = event.data.to_dict()
    user_id = event.params['userId']
    
    try:
        sanitized_email = re.sub(
            r"[@\.]|([^a-zA-Z0-9_-])", 
            lambda m: '_at_' if m.group(0) == '@' else '_dot_' if m.group(0) == '.' else '',
            user_data.get('email', '')
        )
        
        doc_id = f"{sanitized_email}-{user_id}"
        firestore_client = firestore.client()
        user_ref = firestore_client.document(f"users/{doc_id}")

        user_ref.set({
            'uid': user_id,
            'email': user_data.get('email', ''),
            'createdAt': datetime.now(),
            'lastLogin': datetime.now(),
            'lastJob': None
        })

    except Exception as e:
        print(f"Error creating user document: {str(e)}")
        raise

def generate_signed_url(bucket_name, blob_name, expiration_days=182): # 6 months
    """Generate a v4 signed URL for reading a blob."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(days=expiration_days),
        method="GET"
    )

    return url

@https_fn.on_call()
def get_file_url(req: https_fn.CallableRequest) -> dict:
    # Authentication check
    if not req.auth:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.FAILED_PRECONDITION,
            message="Authentication required"
        )
    
    # Generate URL
    url = generate_signed_url(
        bucket_name="your-bucket-name",
        blob_name="path/to/file.txt"
    )
    
    return {"url": url}

# if __name__ == "__main__":
#     from flask import Flask, request
#     app = Flask(__name__)
    
#     @app.route("/", methods=["POST"])
#     def handle_request():
#         return "Hello World"
    
#     app.run(host='0.0.0.0', port=8080)