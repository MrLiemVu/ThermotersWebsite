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

# Initialize Firebase Admin SDK
try:
    # Check if app is already initialized
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        # Use default credentials for local development
        app = initialize_app()
    else:
        cred_path = os.path.abspath(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"Service account key file not found at {cred_path}")
        cred = credentials.Certificate(cred_path)
        app = initialize_app(credential=cred)
except Exception as e:
    logger.warning(f"Firebase initialization warning: {e}")
    app = initialize_app()

# Access Firestore through the default app
db = firestore.client(app)

JOB_STATUS = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed',
    'ERROR': 'error'
}

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
        
        # Extract parameters
        sequence = data.get('sequence', '').upper().strip()
        file_content = data.get('fileContent')
        file_name = data.get('fileName')
        model = data.get('model', 'models/fitted_on_Pr/model_[3]_stm+flex+cumul+rbs.dmp')
        job_title = data.get('jobTitle', 'Untitled Job')
        predictors = data.get('predictors', {})
        is_plus_one = data.get('isPlusOne', True)
        is_rc = data.get('isRc', False)
        max_value = data.get('maxValue', -2.5)
        min_value = data.get('minValue', -6)
        threshold = data.get('threshold', -2.5)
        is_prefix_suffix = data.get('isPrefixSuffix', True)

        # Handle file upload
        if file_content and file_name:
            file_ext = os.path.splitext(file_name)[1].lower()
            sequences = process_file_content(file_content, file_ext)
            if not sequences:
                raise ValueError("No valid sequences found in uploaded file")
            sequence = sequences[0]  # Use first sequence
        elif not sequence:
            raise ValueError("No sequence provided")

        # Validate sequence
        if not re.match(r'^[ACGTU]+$', sequence):
            raise ValueError("Invalid characters in sequence. Only A, C, G, T, U are allowed.")
        
        if len(sequence) < 10:
            raise ValueError("Sequence too short. Minimum length is 10 nucleotides.")

        # Validate model path
        if not os.path.exists(model):
            raise ValueError(f"Model file not found: {model}")

        # Get current month-year
        current_month = datetime.now().strftime("%Y-%m")

        # Get user document
        user_id = req.auth.uid
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            # Create user document if it doesn't exist
            user_ref.set({
                'uid': user_id,
                'createdAt': datetime.now(),
                'lastLogin': datetime.now(),
                'monthlyUsage': {
                    'count': 0,
                    'monthYear': current_month
                }
            })
            user_doc = user_ref.get()

        user_data = user_doc.to_dict()
        
        # Reset counter if new month
        if user_data.get('monthlyUsage', {}).get('monthYear') != current_month:
            user_ref.update({
                'monthlyUsage': {
                    'count': 0,
                    'monthYear': current_month
                }
            })
        else:
            # Check limit
            current_count = user_data.get('monthlyUsage', {}).get('count', 0)
            if current_count >= 100:
                return https_fn.Response(
                    status=429,
                    headers={"Content-Type": "application/json"},
                    response=json.dumps({"error": "Monthly limit of 100 sequences reached"}),
                )

        # Increment counter
        user_ref.update({
            'monthlyUsage.count': current_count + 1
        })

        # Create new job document
        job_ref = db.collection('users').document(user_id).collection('jobhistory').document(job_title)
        job_ref.set({
            'uid': user_id,
            'brickplot': True,
            'jobTitle': job_title,
            'predictors': predictors,
            'sequence': sequence,
            'rc': is_rc,
            'plusOne': is_plus_one,
            'prefixSuffix': is_prefix_suffix,
            'maxValue': max_value,
            'minValue': min_value,
            'threshold': threshold,
            'uploadedAt': datetime.now(),
            'status': 'processing',
        })

        # Generate the brickplot
        try:
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
            
            # Update job status to completed
            job_ref.update({
                'status': 'completed',
                'brickplot': brickplot
            })

            return https_fn.Response(
                status=200,
                headers={"Content-Type": "application/json"},
                response=json.dumps({
                    "message": "Job completed successfully",
                    "jobId": job_ref.id,
                    "brickplot": brickplot
                }),
            )
            
        except Exception as e:
            logger.error(f"Error generating brickplot: {e}")
            job_ref.update({
                'status': 'error',
                'error': str(e)
            })
            raise

    except ValueError as e:
        return https_fn.Response(
            status=400,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"error": str(e)}),
        )
    except Exception as e:
        logger.error(f"Unexpected error in submit_job: {e}")
        return https_fn.Response(
            status=500,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"error": "Internal server error"}),
        )

def get_brickplot(model, sequence, is_plus_one=True, 
                  is_rc=False, max_value=-2.5, min_value=-6,
                  threshold=-2.5, is_prefix_suffix=True):
    """Get the brickplot for a given sequence"""
    logger.info(f"Getting brickplot for sequence: {sequence[:20]}...")
    
    try:
        output_folder = "brickplots"
        brickplotter = BrickPlotter(
            model=model,
            output_folder=output_folder,
            is_plus_one=is_plus_one,
            is_rc=is_rc,
            max_value=max_value,
            min_value=min_value,
            threshold=threshold,
            is_prefix_suffix=is_prefix_suffix
        )
        
        brickplot = brickplotter.get_brickplot(sequence)
        logger.info("Brickplot generated successfully")
        return brickplot
        
    except Exception as e:
        logger.error(f"Error in get_brickplot: {e}")
        raise ValueError(f"Failed to generate brickplot: {e}")

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
            if re.match(r'^[ACGTU]+$', seq):
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
                seq = ''.join(current_seq).upper()
                if re.match(r'^[ACGTU]+$', seq):
                    sequences.append(seq)
                current_seq = []
        else:
            current_seq.append(line.upper().replace(' ', ''))

    # Add the last sequence
    if current_seq:
        seq = ''.join(current_seq).upper()
        if re.match(r'^[ACGTU]+$', seq):
            sequences.append(seq)

    return sequences

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
