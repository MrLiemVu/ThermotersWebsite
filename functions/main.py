"""Main entry point for Thermoters Firebase Functions."""
from __future__ import annotations

import base64
import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from types import SimpleNamespace
from uuid import uuid4

from dotenv import load_dotenv

FORCE_ADMIN_STUBS = os.getenv("THERMOTERS_FORCE_FIREBASE_ADMIN_STUBS", "0").lower() in {"1", "true", "yes"}
USING_FIREBASE_ADMIN_STUBS = False
if not FORCE_ADMIN_STUBS:
    try:
        from firebase_admin import credentials, firestore, get_app, initialize_app
    except ModuleNotFoundError:  # pragma: no cover - local test fallback
        FORCE_ADMIN_STUBS = True

if FORCE_ADMIN_STUBS:
    if __package__:
        from ._stubs import firebase_admin as firebase_admin_stub  # type: ignore
    else:
        import importlib
        firebase_admin_stub = importlib.import_module('_stubs.firebase_admin')
    credentials = firebase_admin_stub.credentials
    firestore = firebase_admin_stub.firestore
    get_app = firebase_admin_stub.get_app
    initialize_app = firebase_admin_stub.initialize_app
    USING_FIREBASE_ADMIN_STUBS = True

FORCE_FUNCTIONS_STUBS = os.getenv("THERMOTERS_FORCE_FUNCTIONS_STUBS", "0").lower() in {"1", "true", "yes"}
USING_FIREBASE_STUBS = False
if not FORCE_FUNCTIONS_STUBS:
    try:
        from firebase_functions import https_fn, identity_fn  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover - executed only in local test environments without the SDK
        FORCE_FUNCTIONS_STUBS = True

if FORCE_FUNCTIONS_STUBS:
    if __package__:
        from ._stubs import firebase_functions as firebase_functions_stub  # type: ignore
    else:
        import importlib
        firebase_functions_stub = importlib.import_module('_stubs.firebase_functions')
    https_fn = firebase_functions_stub.https_fn
    identity_fn = firebase_functions_stub.identity_fn
    USING_FIREBASE_STUBS = True
else:
    USING_FIREBASE_STUBS = False


if __package__:
    from .src.BrickPlotter import BrickPlotter
else:  # Script execution fallback to support `python main.py`
    from src.BrickPlotter import BrickPlotter

load_dotenv()  # Load environment variables from .env file
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if USING_FIREBASE_STUBS:  # Surface a helpful hint during local development
    logger.warning(
        "firebase_functions package not installed; using lightweight stubs. "
        "Install firebase-functions to run inside the managed environment."
    )

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DEFAULT_MODEL = MODELS_DIR / "fitted_on_Pr" / "model_[3]_stm+flex+cumul+rbs.dmp"




def _activate_admin_stubs(reason: Exception | str):
    """Switch firebase_admin references to the lightweight stubs."""
    global credentials, firestore, get_app, initialize_app, USING_FIREBASE_ADMIN_STUBS
    logger.warning("Falling back to firebase_admin stubs: %s", reason)
    if __package__:
        from ._stubs import firebase_admin as firebase_admin_stub  # type: ignore
    else:
        import importlib
        firebase_admin_stub = importlib.import_module('_stubs.firebase_admin')
    credentials = firebase_admin_stub.credentials
    firestore = firebase_admin_stub.firestore
    get_app = firebase_admin_stub.get_app
    initialize_app = firebase_admin_stub.initialize_app
    USING_FIREBASE_ADMIN_STUBS = True
    return firebase_admin_stub

def _serialize_for_json(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_for_json(item) for item in value]
    return value

def _resolve_path(path_like: str | os.PathLike[str]) -> Path:
    """Resolve a path relative to the functions package directory."""
    path = Path(path_like)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path

def _initialise_firebase_app() -> Any:
    """Initialise the Firebase Admin SDK exactly once."""
    try:
        return get_app()
    except ValueError:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path:
            candidate = _resolve_path(cred_path)
            try:
                credentials_obj = credentials.Certificate(candidate)
                return initialize_app(credential=credentials_obj)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Falling back to default credentials: %s", exc)
        return initialize_app()


app = _initialise_firebase_app()
try:
    db = firestore.client(app)
except Exception as exc:
    if USING_FIREBASE_ADMIN_STUBS:
        raise
    firebase_admin_stub = _activate_admin_stubs(exc)
    app = initialize_app()
    db = firebase_admin_stub.firestore.client(app)

def _resolve_auth_provider(user: Any) -> str:
    for attr in ("provider_id", "providerId", "sign_in_provider", "signInProvider"):
        value = getattr(user, attr, None)
        if value:
            return str(value)
    return "unknown"


def _build_user_profile(uid: str, email: Optional[str], auth_provider: Optional[str]) -> Dict[str, Any]:
    now = datetime.now()
    return {
        "uid": uid,
        "email": email,
        "authProvider": auth_provider or "unknown",
        "createdAt": now,
        "lastLogin": now,
        "firstJob": None,
        "lastJob": None,
        "monthlyUsage": {"count": 0, "monthYear": now.strftime("%Y-%m")}
    }

JOB_STATUS = {
    "PENDING": "pending",
    "PROCESSING": "processing",
    "COMPLETED": "completed",
    "ERROR": "error",
}


def _model_path_from_request(model_path: Optional[str]) -> Path:
    """Resolve and validate the requested model path."""
    candidate = Path(model_path) if model_path else DEFAULT_MODEL
    candidate = _resolve_path(candidate)
    if not candidate.exists():
        raise ValueError(f"Model file not found: {candidate}")
    return candidate


def _decode_test_auth(req: Any) -> None:
    """Inject a mock auth object when running under the local test harness."""
    if req.headers.get("X-Test-Auth") == "true":
        token = req.headers.get("Authorization", "").replace("Bearer ", "")
        provider = req.headers.get("X-Test-Provider", "test-provider")
        email = req.headers.get("X-Test-Email")
        req.auth = type("MockAuth", (), {"uid": "test_user_123", "token": token, "provider": provider, "email": email})()


@https_fn.on_request(region="europe-west2")
def get_job_history(req: https_fn.Request) -> https_fn.Response:
    """Return the job history for the requested user."""
    _decode_test_auth(req)
    if not getattr(req, "auth", None):
        return https_fn.Response(
            status=401,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"error": "Unauthorized"}),
        )

    try:
        data = req.get_json() or {}
    except Exception:
        data = {}

    args = getattr(req, "args", {}) or {}
    user_id = data.get("userId") or args.get("userId") or getattr(req.auth, "uid", None)  # type: ignore[attr-defined]
    if not user_id:
        return https_fn.Response(
            status=400,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"error": "userId is required"}),
        )

    try:
        jobs_collection = db.collection('users').document(user_id).collection('jobhistory')
        direction_desc = getattr(getattr(firestore, 'Query', SimpleNamespace(DESCENDING='DESCENDING')), 'DESCENDING', 'DESCENDING')
        try:
            snapshots = jobs_collection.order_by('uploadedAt', direction=direction_desc).stream()
        except Exception:
            snapshots = jobs_collection.stream()

        entries = []
        for snapshot in snapshots:
            doc_dict = snapshot.to_dict()
            sort_key = doc_dict.get('uploadedAt')
            entries.append((sort_key, snapshot.id, doc_dict))

        entries.sort(key=lambda item: item[0] or datetime.min, reverse=True)

        job_history = []
        for sort_key, doc_id, doc_dict in entries:
            serialised = _serialize_for_json(doc_dict)
            serialised['id'] = doc_id
            job_history.append(serialised)

        return https_fn.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"jobs": job_history}),
        )
    except Exception as exc:
        logger.exception("Error fetching job history: %s", exc)
        return https_fn.Response(
            status=500,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"error": "Failed to load job history"}),
        )


@https_fn.on_request(region="europe-west2")
def submit_job(req: https_fn.Request) -> https_fn.Response:
    """Submit a job to the API."""
    _decode_test_auth(req)
    if not getattr(req, "auth", None):
        return https_fn.Response(
            status=401,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"error": "Unauthorized"}),
        )

    try:
        data = req.get_json()
        logger.info("Submit Job - Received request data: %s", data)

        sequence = (data.get("sequence", "") or "").upper().strip()
        file_content = data.get("fileContent")
        file_name = data.get("fileName")
        model_path = _model_path_from_request(data.get("model"))
        job_title = data.get("jobTitle", "Untitled Job")
        predictor_label = data.get("predictor") or "standard"
        predictors_payload = data.get("predictors") or {}
        predictors = {
            "standard": bool(predictors_payload.get("standard", predictor_label == "standard")),
            "standardSpacer": bool(predictors_payload.get("standardSpacer")),
            "standardSpacerCumulative": bool(predictors_payload.get("standardSpacerCumulative")),
        }
        is_plus_one = data.get("isPlusOne", True)
        is_rc = data.get("isRc", False)
        max_value = data.get("maxValue", -2.5)
        min_value = data.get("minValue", -6)
        threshold = data.get("threshold", -2.5)
        is_prefix_suffix = data.get("isPrefixSuffix", True)

        if file_content and file_name:
            file_ext = os.path.splitext(file_name)[1].lower()
            sequences = process_file_content(file_content, file_ext)
            if not sequences:
                raise ValueError("No valid sequences found in uploaded file")
            sequence = sequences[0]
        elif not sequence:
            raise ValueError("No sequence provided")

        if not re.fullmatch(r"[ACGTU]+", sequence):
            raise ValueError("Invalid characters in sequence. Only A, C, G, T, U are allowed.")
        if len(sequence) < 10:
            raise ValueError("Sequence too short. Minimum length is 10 nucleotides.")

        current_month = datetime.now().strftime("%Y-%m")
        user_id = req.auth.uid  # type: ignore[attr-defined]
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            user_ref.set(
                _build_user_profile(
                    uid=user_id,
                    email=data.get("email") or getattr(getattr(req, "auth", object()), "email", None),
                    auth_provider=getattr(getattr(req, "auth", object()), "provider", None),
                ),
                merge=True,
            )
            user_doc = user_ref.get()

        user_data = (user_doc.to_dict() or {}) if hasattr(user_doc, "to_dict") else {}
        monthly_usage = user_data.get("monthlyUsage", {})
        previous_last_job = user_data.get("lastJob")
        stored_month = monthly_usage.get("monthYear")
        current_count = monthly_usage.get("count", 0)

        if stored_month != current_month:
            current_count = 0
            user_ref.update({
                "monthlyUsage": {"count": current_count, "monthYear": current_month}
            })
        elif current_count >= 100:
            return https_fn.Response(
                status=429,
                headers={"Content-Type": "application/json"},
                response=json.dumps({"error": "Monthly limit of 100 sequences reached"}),
            )

        user_ref.update({"monthlyUsage.count": current_count + 1})

        job_collection = (
            db.collection("users")
            .document(user_id)
            .collection("jobhistory")
        )
        job_id = data.get("jobId") or f"job_{uuid4().hex}"
        job_ref = job_collection.document(job_id)
        job_ref.set(
            {
                "uid": user_id,
                "jobTitle": job_title,
                "nextTitle": None,
                "predictor": predictor_label,
                "predictors": predictors,
                "sequence": sequence,
                "brickplot": None,
                "status": JOB_STATUS["PROCESSING"],
                "uploadedAt": datetime.now(),
                "rc": is_rc,
                "plusOne": is_plus_one,
                "prefixSuffix": is_prefix_suffix,
                "maxValue": max_value,
                "minValue": min_value,
                "threshold": threshold,
            }
        )

        if previous_last_job and previous_last_job != job_id:
            job_collection.document(previous_last_job).update({"nextTitle": job_id})

        user_updates = {"lastJob": job_id, "lastLogin": datetime.now()}
        if not user_data.get("firstJob"):
            user_updates["firstJob"] = job_id
        user_ref.update(user_updates)

        try:
            brickplot = get_brickplot(
                model=str(model_path),
                sequence=sequence,
                is_plus_one=is_plus_one,
                is_rc=is_rc,
                max_value=max_value,
                min_value=min_value,
                threshold=threshold,
                is_prefix_suffix=is_prefix_suffix,
            )
            job_ref.update({"status": JOB_STATUS["COMPLETED"], "brickplot": brickplot})
            return https_fn.Response(
                status=200,
                headers={"Content-Type": "application/json"},
                response=json.dumps(
                    {
                        "message": "Job completed successfully",
                        "jobId": job_ref.id,
                        "brickplot": brickplot,
                    }
                ),
            )
        except Exception as exc:
            logger.error("Error generating brickplot: %s", exc)
            job_ref.update({"status": JOB_STATUS["ERROR"], "error": str(exc)})
            raise

    except ValueError as exc:
        return https_fn.Response(
            status=400,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"error": str(exc)}),
        )
    except Exception as exc:  # pragma: no cover - defensive logging of unexpected errors
        logger.exception("Unexpected error in submit_job: %s", exc)
        return https_fn.Response(
            status=500,
            headers={"Content-Type": "application/json"},
            response=json.dumps({"error": "Internal server error"}),
        )


def get_brickplot(
    *,
    model: str,
    sequence: str,
    is_plus_one: bool = True,
    is_rc: bool = False,
    max_value: float = -2.5,
    min_value: float = -6,
    threshold: float = -2.5,
    is_prefix_suffix: bool = True,
) -> Dict[str, Any]:
    """Generate the brickplot for a given sequence."""
    logger.info("Generating brickplot for sequence prefix: %s", sequence[:20])
    output_dir = BASE_DIR / "brickplots"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        brickplotter = BrickPlotter(
            model=model,
            output_folder=str(output_dir),
            is_plus_one=is_plus_one,
            is_rc=is_rc,
            max_value=max_value,
            min_value=min_value,
            threshold=threshold,
            is_prefix_suffix=is_prefix_suffix,
        )
        return brickplotter.get_brickplot(sequence)
    except Exception as exc:
        logger.error("Error in get_brickplot: %s", exc)
        raise ValueError(f"Failed to generate brickplot: {exc}")


@identity_fn.before_user_created(region="europe-west2")
def create_user_document(event: identity_fn.AuthBlockingEvent):
    """Create the initial Firestore user document and placeholder job."""
    user = event.data
    logger.info("Starting user bootstrap for UID %s", getattr(user, "uid", "<unknown>"))

    try:
        user_id = user.uid
        batch = db.batch()
        user_ref = db.collection("users").document(user_id)
        job_ref = user_ref.collection("jobhistory").document("placeholder")

        batch.set(
            user_ref,
            _build_user_profile(
                uid=user.uid,
                email=getattr(user, "email", None),
                auth_provider=_resolve_auth_provider(user),
            ),
            merge=True,
        )

        batch.set(
            job_ref,
            {
                "uid": user.uid,
                "jobTitle": "placeholder",
                "nextTitle": None,
                "predictor": None,
                "predictors": {
                    "standard": False,
                    "standardSpacer": False,
                    "standardSpacerCumulative": False,
                },
                "sequence": "",
                "status": "placeholder",
                "brickplot": None,
                "uploadedAt": datetime.now(),
            },
        )

        batch.commit()
        logger.info("Successfully created user bootstrap data for %s", user.uid)
        return identity_fn.BeforeCreateResponse()
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("create_user_document failed: %s", exc)
        return identity_fn.BeforeCreateResponse()


def generate_signed_url(bucket_name: str, blob_name: str, expiration_days: int = 182) -> str:
    """Generate a V4 signed URL for a blob."""
    if storage is None:  # pragma: no cover - requires google-cloud-storage at runtime
        raise RuntimeError("google-cloud-storage is required to generate signed URLs")

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(
        version="v4", expiration=timedelta(days=expiration_days), method="GET"
    )


def handle_image(brick_data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """Return inline image data or persist large payloads to Cloud Storage."""
    logger.info("Handling image for job %s", job_id)
    image_bytes = base64.b64decode(brick_data["image_base64"])

    if len(image_bytes) > 1_000_000:  # 1 MB threshold
        if storage is None:  # pragma: no cover - requires google-cloud-storage at runtime
            raise RuntimeError("google-cloud-storage is required to persist brickplot images")
        bucket = storage.Client().bucket("thermoters-jobs")
        blob = bucket.blob(f"images/{job_id}.png")
        blob.upload_from_string(image_bytes, content_type="image/png")
        return {"url": blob.generate_signed_url(3600)}

    return {"image": brick_data["image_base64"]}


def process_file_content(content: str, file_extension: str) -> list[str]:
    """Process uploaded files to extract DNA sequences."""
    logger.info("Processing uploaded content (extension=%s)", file_extension)
    file_extension = file_extension.lower()

    if file_extension == ".csv":
        return process_csv(content)
    if file_extension in [".fna", ".ffn", ".faa", ".fasta"]:
        return process_fasta(content)
    raise ValueError(f"Unsupported file type: {file_extension}")


def process_csv(content: str) -> list[str]:
    """Extract sequences from CSV content."""
    import csv
    from io import StringIO

    sequences: list[str] = []
    reader = csv.DictReader(StringIO(content))
    for row in reader:
        seq = (row.get("sequence") or "").upper().replace(" ", "")
        if seq and re.fullmatch(r"[ACGTU]+", seq):
            sequences.append(seq)
    return sequences


def process_fasta(content: str) -> list[str]:
    """Extract sequences from FASTA-like content."""
    sequences: list[str] = []
    current_seq: list[str] = []

    for line in content.splitlines():
        line = line.strip()
        if line.startswith(">"):
            if current_seq:
                candidate = "".join(current_seq).upper()
                if re.fullmatch(r"[ACGTU]+", candidate):
                    sequences.append(candidate)
                current_seq = []
        elif line:
            current_seq.append(line.upper().replace(" ", ""))

    if current_seq:
        candidate = "".join(current_seq).upper()
        if re.fullmatch(r"[ACGTU]+", candidate):
            sequences.append(candidate)

    return sequences


@https_fn.on_request(region="europe-west2")
def ping(req: https_fn.Request) -> https_fn.Response:  # noqa: D401 - short response helper
    """Simple health-check endpoint."""
    return https_fn.Response(
        status=200,
        headers={"Content-Type": "application/json"},
        response=json.dumps(
            {"status": "success", "message": f"Ping received at {datetime.now().isoformat()}"}
        ),
    )
