""" Main function for the Thermoters API """
import os
import re
import base64
import json
import logging
from datetime import datetime, timedelta
from firebase_functions import https_fn, firestore_fn, identity_fn
from BrickPlotter import BrickPlotter
from google.cloud import storage
from dotenv import load_dotenv
from firebase_admin import initialize_app, firestore, credentials


from utils.general_functions import *
from utils.model_functions import *

load_dotenv()  # Load environment variables from .env file
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Thermoters API")
# Validate environment variables
if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

cred_path = os.path.abspath(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
if not os.path.exists(cred_path):
    raise FileNotFoundError(f"Service account key file not found at {cred_path}")

cred = credentials.Certificate(cred_path)

# Initialize Firebase Admin SDK
app = initialize_app(credential=cred)

# Access Firestore through the default app
db = firestore.client(app)

JOB_STATUS = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed',
    'ERROR': 'error'
}

# Modify the submit_job decorator
@https_fn.on_request(region="europe-west2")
def submit_job(req: https_fn.Request) -> https_fn.Response:
    """Submit a job to the API"""
    # Authentication check
    if req.headers.get('X-Test-Auth') == 'true':
        # Create a mock auth object for testing
        req.auth = type('MockAuth', (), {
            'uid': 'test_user_123',
            'token': req.headers.get('Authorization', '').replace('Bearer ', '')
        })
    elif not req.auth:
        return https_fn.Response(
            status=401,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"error": "Unauthorized"}),
        )

    try:
        data = req.get_json()
        logger.info(f"Submit Job - Received request data: {data}")
        # Check for file upload
        if 'fileContent' in data and 'fileName' in data:
            file_content = data['fileContent']
            file_name = data['fileName']
            file_ext = os.path.splitext(file_name)[1]

            sequences = process_file_content(file_content, file_ext)
            if not sequences:
                raise ValueError("No valid sequences found in uploaded file")
            sequence = sequences[0]  # Use first sequence
        else:
            sequence = str(data.get('sequence', '')).upper()

        model = data.get('model')
        job_title = data.get('job_title')
        predictors = data.get('predictors')
        is_plus_one = data.get('is_plus_one', True)
        is_rc = data.get('is_rc', False)
        max_value = data.get('max_value', -2.5)
        min_value = data.get('min_value', -6)
        threshold = data.get('threshold', -2.5)
        is_prefix_suffix = data.get('is_prefix_suffix', True)

        # Validate input
        if not sequence or len(sequence) < 10:
            raise ValueError("Invalid sequence input")

        # Get current month-year
        current_month = datetime.now().strftime("%Y-%m")

        # Get user document
        user_id = req.auth.uid
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get().to_dict()

        # # Reset counter if new month
        # if user_doc['monthlyUsage']['monthYear'] != current_month:
        #     user_ref.update({
        #         'monthlyUsage': {
        #             'count': 0,
        #             'monthYear': current_month
        #         }
        #     })
        # else:
        #     # Check limit
        #     if user_doc['monthlyUsage']['count'] >= 100:
        #         return https_fn.Response(
        #             status=429,
        #             headers={"Content-Type": "application/json"},
        #             response=json.dumps({"error": "Monthly limit of 100 sequences reached"}),
        #         )

        # # Increment counter
        # user_ref.update({
        #     'monthlyUsage.count': user_doc['monthlyUsage']['count'] + 1
        # })

        # # Get Predictors
        # # Create new job document
        # job_ref = db.collection('users').document(user_id).collection('jobhistory').document(job_title)
        # job_ref.set({
        #     'uid': user_id,
        #     'brickplot': True,
        #     'jobTitle': job_title,
        #     'predictors': predictors,
        #     'sequence': sequence,
        #     'rc': is_rc,
        #     'plusOne': is_plus_one,
        #     'prefixSuffix': is_prefix_suffix,
        #     'maxValue': max_value,
        #     'minValue': min_value,
        #     'threshold': threshold,
        #     'uploadedAt': datetime.now(),
        #     'status': 'completed',
        # })

        # Get the brickplot
        brickplot = get_brickplot(
            model=model,
            sequence=sequence,
            is_plus_one=is_plus_one,
            is_rc=is_rc,
            max_value=max_value,
            min_value=min_value,
            threshold=threshold,
            is_prefix_suffix=is_prefix_suffix
        )

        return https_fn.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            response=json.dumps({
                "message": "Job submitted",
                "jobId": 1,#job_ref.id,
                "brickplot": brickplot
            }),
        )

    except ValueError as e:
        return https_fn.Response(
            status=400,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"error": f"File processing error: {str(e)}"}),
        )

def get_brickplot(model, sequence, is_plus_one=True, 
                  is_rc=False, max_value=-2.5, min_value=-6,
                  threshold=-2.5, is_prefix_suffix=True):
    """Get the brickplot for a given sequence"""
    logger.info(f"Getting brickplot for sequence: {sequence}")
    output_folder = "brickplots"
    brickplotter = BrickPlotter(model=model,
                                output_folder=output_folder,
                                is_plus_one=is_plus_one,
                                is_rc=is_rc,
                                max_value=max_value,
                                min_value=min_value,
                                threshold=threshold,
                                is_prefix_suffix=is_prefix_suffix
                                )
    brickplot = brickplotter.get_brickplot(sequence)
    return brickplot

@identity_fn.before_user_created(region="europe-west2")
def create_user_document(event: identity_fn.AuthBlockingEvent):
    """Creates user document and placeholder job with atomic writes"""
    logger.info(f"[DEBUG] Auth trigger started for UID: {event.data.uid}")
    logger.info(f"User email: {event.data.email}")
    user = event.data
    try:
        user_id = user.uid
        
        # Get Firestore batch
        batch = db.batch()
        user_ref = db.collection('users').document(user_id)
        job_ref = user_ref.collection('jobhistory').document('placeholder')

        # User document data
        batch.set(user_ref, {
            'uid': user.uid,
            'email': user.email,
            'createdAt': datetime.now(),
            'lastLogin': datetime.now(),
            'monthlyUsage': {
                'count': 0,
                'monthYear': datetime.now().strftime("%Y-%m")
            }
        }, merge=True)

        # Placeholder job data
        batch.set(job_ref, {
            'uid': user.uid,
            'brickplot': False,
            'jobTitle': 'placeholder',
            'predictors': {'standard': False, 'standardSpacer': False, 
                          'standardSpacerCumulative': False, 'extended': False},
            'sequence': 'ACTG',
            'rc': False,
            'plusOne': False,
            'prefixSuffix': False,
            'maxValue': -2.5,
            'minValue': -6,
            'threshold': -2.5,
            'uploadedAt': datetime.now(),
            'status': 'initialized',
        })

        # Atomic commit
        batch.commit()
        logger.info(f"Successfully created user document for {user.uid}")
        # Return explicit success to ensure function completes
        return identity_fn.BeforeCreateResponse()
    except Exception as e:
        logger.error(f"Critical error creating user document: {str(e)}", exc_info=True)
        # Still allow user creation even if Firestore operations fail
        return identity_fn.BeforeCreateResponse()

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

def handle_image(brick_data, job_id):
    """Smart image handling with fallback"""
    logger.info(f"Handling image for job: {job_id}")
    image_bytes = base64.b64decode(brick_data['image_base64'])

    if len(image_bytes) > 1_000_000:  # 1MB threshold
        # Store large images in Cloud Storage
        bucket = storage.Client().bucket("thermoters-jobs")
        blob = bucket.blob(f"images/{job_id}.png")
        blob.upload_from_string(image_bytes, content_type="image/png")
        return {'url': blob.generate_signed_url(3600)}  # 1hr access
    else:
        # Return small images directly
        return {'image': brick_data['image_base64']}

def process_file_content(content: str, file_extension: str) -> list:
    """Process different file types to extract DNA sequences"""
    logger.info(f"Processing file content with extension: {file_extension}")
    file_extension = file_extension.lower()

    if file_extension == '.csv':
        return process_csv(content)
    elif file_extension in ['.fna', '.ffn', '.faa', '.fasta']:
        return process_fasta(content)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def process_csv(content: str) -> list:
    """Process CSV files to extract sequences"""
    logger.info("Processing CSV file")
    import csv
    from io import StringIO

    sequences = []
    reader = csv.DictReader(StringIO(content))

    for row in reader:
        if 'sequence' in row:
            seq = row['sequence'].upper().replace(' ', '')
            sequences.append(seq)

    return sequences

def process_fasta(content) -> list:
    """Process FASTA files to extract sequences"""
    logger.info("Processing FASTA file")
    sequences = []
    current_seq = []

    # Split the input content by newlines
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('>'):
            if current_seq:
                sequences.append(''.join(current_seq))
                current_seq = []
        else:
            current_seq.append(line.upper().replace(' ', ''))

    # Add the last sequence
    if current_seq:
        sequences.append(''.join(current_seq))

    return sequences

# # Add health check handler
# @https_fn.on_request()
# def health_check(req: https_fn.Request) -> https_fn.Response:
#     return https_fn.Response(
#         status=200,
#         headers={"Content-Type": "text/plain", "Access-Control-Allow-Origin": "*"},
#         response="OK"
#     )

@https_fn.on_request(region="europe-west2")
def ping(req: https_fn.Request) -> https_fn.Response:
    """Health check endpoint that returns 200 OK"""
    return https_fn.Response(
        status=200,
        headers={"Content-Type": "application/json"},
        response=json.dumps({
            "status": "success",
            "message": "Ping received at {}".format(datetime.now().isoformat())
        }),
    )
