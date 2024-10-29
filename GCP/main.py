from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid  # For generating unique file names

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")  # Path to your service account key
firebase_admin.initialize_app(cred, {
    'storageBucket': 'thermoterswebsite.appspot.com'  # Replace with your Firebase Storage bucket
})
db = firestore.client()  # Firestore client
bucket = storage.bucket()  # Firebase Storage bucket

app = Flask(__name__)

@app.route("/", methods=["POST"])
def run_algorithm():
    data = request.json
    job_title = data.get('jobtitle')
    sequence = data.get('sequence')
    predictors = data.get('predictors')
    brickplot = data.get('brickplot')

    # Run your algorithm function
    result = generate_brickplot(sequence, predictors, brickplot)

    # Save result to Firebase Storage and Firestore
    try:
        file_url = save_result_to_storage(job_title, result)
        store_result_in_firestore(job_title, file_url)
    except Exception as e:
        print(f"Error saving to Firestore or Storage: {e}")
        return jsonify({"error": "Failed to save result"}), 500

    return jsonify({
        "job_title": job_title,
        "result_url": file_url,
    })

def generate_brickplot(sequence, predictors, brickplot):
    pass

def save_result_to_storage(job_title, result):
    # Convert result to bytes for uploading
    result_bytes = result.encode('utf-8')
    
    # Create a unique filename
    file_name = f"{job_title}_{uuid.uuid4()}.txt"
    blob = bucket.blob(f"results/{file_name}")  # Path in Firebase Storage

    # Upload result as a text file
    blob.upload_from_string(result_bytes, content_type="text/plain")
    
    # Make file publicly accessible (optional, depending on your access rules)
    blob.make_public()

    # Get the public URL of the file
    file_url = blob.public_url
    print("File uploaded to Storage with URL:", file_url)
    return file_url

def store_result_in_firestore(job_title, file_url):
    # Create a new document in the 'job_results' collection
    doc_ref = db.collection("users").document(user).collection("jobhistory").document()   # Generates a unique ID for the document

    # Store data in Firestore with a reference to the Storage file URL
    doc_ref.set({
        "job_title": job_title,
        "result_url": file_url,
        "created_at": firestore.SERVER_TIMESTAMP  # Firestore's server timestamp
    })
    print("Result successfully saved to Firestore with URL")