from cloudevents.http import CloudEvent
import functions_framework
from google.cloud import firestore
from google.cloud import storage
from BrickPlotter import BrickPlotter

def upload_image_to_bucket(bucket_name, source_file_path, destination_blob_name):
    """Uploads a file to Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_path)
    print(f"File {source_file_path} uploaded to {destination_blob_name}.")

def generate_signed_url(bucket_name, blob_name, expiration_time=15724800): # 6 months in seconds
    """Generates a signed URL for accessing a private GCS object."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(expiration=expiration_time)
    print(f"Signed URL: {url}")
    return url

@functions_framework.cloud_event
def process_request(cloud_event: CloudEvent) -> None:
    """Triggers by a change to a Firestore document.
    Args:
        cloud_event: CloudEvent with information on the Firestore event trigger
    """
    try:
        # 1. Parse Firestore event payload
        firestore_payload = firestore.DocumentEventData()
        firestore_payload._pb.ParseFromString(cloud_event.data)

        # Extract information from Firestore payload
        document_data = firestore_payload.value.fields
        modelname = document_data["model"].string_value
        output_folder = document_data["output_folder"].string_value
        is_plus_one = document_data["is_plus_one"].boolean_value
        is_rc = document_data["is_rc"].boolean_value
        max_value = document_data["max_value"].double_value
        min_value = document_data["min_value"].double_value
        is_high_to_default = document_data["is_high_to_default"].boolean_value
        threshold = document_data["threshold"].double_value
        is_prefix_suffix = document_data["is_prefix_suffix"].boolean_value
        input_file_path = document_data["input_file"].string_value

        # 2. Initialize BrickPlotter
        brickplotter = BrickPlotter(
            model=modelname,
            output_folder=output_folder,
            is_plus_one=is_plus_one,
            is_rc=is_rc,
            max_value=max_value,
            min_value=min_value,
            is_high_to_default=is_high_to_default,
            threshold=threshold,
            is_prefix_suffix=is_prefix_suffix
        )

        # 3. Download input file from Cloud Storage
        storage_client = storage.Client()
        bucket_name, input_blob_path = input_file_path.replace("gs://", "").split("/", 1)
        bucket = storage_client.bucket(bucket_name)
        input_blob = bucket.blob(input_blob_path)

        local_input_file = f"/tmp/{input_blob_path.split('/')[-1]}"
        input_blob.download_to_filename(local_input_file)

        # 4. Generate Brick plot
        figures = brickplotter.get_brickplot(local_input_file)

        # 5. Save generated plots to Cloud Storage and generate signed URLs
        output_bucket = storage_client.bucket(bucket_name)
        signed_urls = []
        for i, figure in enumerate(figures):
            local_output_file = f"/tmp/figure_{i}.png"
            figure.save(local_output_file)

            output_blob_name = f"{output_folder}/figure_{i}.png"
            output_blob = output_bucket.blob(output_blob_name)
            upload_image_to_bucket(bucket_name, local_output_file, output_blob_name)

            signed_url = generate_signed_url(bucket_name, output_blob_name)
            signed_urls.append(signed_url)

        print("Successfully processed and uploaded brick plots.")
        print("Generated Signed URLs:", signed_urls)

        # 6. Update Firestore document with signed URLs
        db = firestore.Client()
        doc_ref = db.document(firestore_payload.value.name)
        doc_ref.update({"signed_urls": signed_urls})

    except Exception as e:
        print(f"Error during processing: {e}")

        # Save the failed input file to a designated "failed" folder in Cloud Storage
        failed_blob = bucket.blob(f"failed/{input_blob_path.split('/')[-1]}")
        failed_blob.upload_from_filename(local_input_file)

        return
