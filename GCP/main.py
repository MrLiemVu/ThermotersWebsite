from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid  # For generating unique file names
import os

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
    data_dict = dict()
    file_id = uuid.uuid4()
    data_dict["fileID"] = file_id
    data_dict["jobTitle"] = data.get('jobtitle')
    data_dict["sequence"]= data.get('sequence')

    # Run your algorithm function
    predictors = data.get('predictors')
    for predictor in predictors:
        data_dict["predictor"] = data.get(predictor)
        brickplot = generate_brickplot(sequence, predictor)
        data_dict["brickplot"] = brickplot
        data_dict["nextJob"] = ""

        # Save result to Firebase Storage and Firestore
        try:
            file_url = save_result_to_storage(brickplot, user_id, file_id)
            data_dict["fileUrl"] = file_url
            store_result_in_firestore(data_dict, user_id)
        except Exception as e:
            print(f"Error saving to Firestore or Storage: {e}")
            return jsonify({"error": "Failed to save result"}), 500

    return 

def store_result_in_firestore(data, user_id):
    
    # Updates Last job + last job's next job
    prev_last_job = db.collection("users").document(user_id).get("lastJob")
    db.collection("users").document(user_id).update({"lastJob": data["fileID"]})
    db.collection("users").document(user_id).collection("history").document(prev_last_job).update({"nextJob": data["fileID"]})
    
    # Create a new document in the 'job_results' collection
    doc_ref = db.collection("users").document(user).collection("history").document(data["fileID"]) 

    # Store data in Firestore with a reference to the Storage file URL
    doc_ref.set({
        "brickplot": data["brickplot"],
        "fileUrl": data["fileUrl"],
        "jobTitle": data["jobTitle"],
        "nextJob": data["nextJob"],
        "predictor": data["predictor"],
        "sequence": data["sequence"],
        "status": 1,
        "uploadedAt": firestore.SERVER_TIMESTAMP  # Firestore's server timestamp
    })
    print("Result successfully saved to Firestore with URL")
    
def save_result_to_storage(data, user_id, file_id):
    # Convert result to bytes for uploading
    result_bytes = result.encode('utf-8')
    
    # Create a unique filename
    file_name = f"{file_id}.txt"
    blob = bucket.blob(f"userdata/{user_id}/{file_id}")  # Path in Firebase Storage

    # Upload result as a text file
    blob.upload_from_string(result_bytes, content_type="text/plain")
    
    # # Make file publicly accessible (optional, depending on your access rules)
    # blob.make_public()

    # Get the public URL of the file
    file_url = blob.public_url
    return file_url

def env_vars(request):
    return os.environ.get(request, "Specified environment variable is not set.")

def generate_brickplot(sequence, predictor):
    pass