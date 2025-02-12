from google.cloud import firestore
from google.cloud import storage
import uuid
import os
import base64
import io
import seaborn as sns
import matplotlib.pyplot as plt

def submit_job(request):
    """HTTP Cloud Function"""
    from flask import jsonify
    
    # Initialize Firestore
    db = firestore.Client()
    
    # Get request data
    request_json = request.get_json(silent=True)
    headers = request.headers
    
    # Authentication check
    if 'Authorization' not in headers:
        return jsonify({"error": "Authentication required"}), 401
        
    # Process request data
    try:
        job_data = request_json
        user_id = headers.get('X-User-ID')
        job_id = str(uuid.uuid4())
        
        # Save to Firestore
        doc_ref = db.collection('users').document(user_id).collection('jobs').document(job_id)
        doc_ref.set({
            'jobId': job_id,
            'userId': user_id,
            'sequence': job_data['sequence'],
            'predictors': job_data['predictors'],
            'jobTitle': job_data['jobTitle'],
            'status': 'pending',
            'createdAt': firestore.SERVER_TIMESTAMP
        })
        
        # Generate results
        results = generate_brickplot(job_data['sequence'])
        
        # Create plot
        fig = plt.figure(figsize=(10, 6))
        sns.lineplot(x=results['positions'], y=results['values'])
        plt.title("Gene Expression Profile")
        plt.xlabel("Position")
        plt.ylabel("Expression Level")
        
        # Convert plot to base64
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

        # Upload to Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket('thermoterswebsite.appspot.com')
        blob = bucket.blob(f"results/{job_id}.png")
        blob.upload_from_string(base64.b64decode(image_base64), content_type='image/png')
        
        # Add URL to Firestore
        doc_ref.update({
            'result_image': f"https://storage.googleapis.com/{bucket.name}/{blob.name}",
            'result_analysis': results['text_analysis']
        })

        return jsonify({
            "status": "success",
            "jobId": job_id,
            "image": f"data:image/png;base64,{image_base64}",
            "analysis": results['text_analysis']
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_brickplot(sequence):
    # Your actual analysis logic here
    return {
        'positions': list(range(len(sequence))),
        'values': [i % 10 for i in range(len(sequence))],  # Example data
        'text_analysis': f"Analysis complete for sequence length {len(sequence)}. Peak expression at position 42."
    } 