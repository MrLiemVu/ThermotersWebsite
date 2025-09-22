"""Unit tests for Firebase function entry points."""
from __future__ import annotations

import base64
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Tuple

import pytest

try:
    from functions import main
except ModuleNotFoundError:  # pragma: no cover - fallback when tests run from repo root
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from functions import main

TEST_DATA_DIR = Path(__file__).resolve().parent
TEXT_SEQUENCE = (TEST_DATA_DIR / 'test_sequence.txt').read_text().strip()
FASTA_SEQUENCE_PATH = TEST_DATA_DIR / 'test_sequence.fasta'
FASTA_SEQUENCE = ''.join(line.strip() for line in FASTA_SEQUENCE_PATH.read_text().splitlines() if not line.startswith('>'))

class FakeSnapshot:
    def __init__(self, doc_id: str, data: Dict[str, Any] | None) -> None:
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> Dict[str, Any]:
        if not self.exists:
            return {}
        data = dict(self._data)
        data.pop("__subcollections__", None)
        return data

def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:

    for key, value in source.items():

        if key == "__subcollections__":

            continue

        if isinstance(value, dict) and isinstance(target.get(key), dict):

            _deep_merge(target[key], value)

        else:

            target[key] = value


class FakeDocument:
    def __init__(self, store: Dict[str, Any], doc_id: str) -> None:
        self._store = store
        self._doc_id = doc_id

    @property
    def id(self) -> str:
        return self._doc_id

    def _ensure_doc(self) -> Dict[str, Any]:
        doc = self._store.setdefault(self._doc_id, {})
        doc.setdefault("__subcollections__", {})
        return doc

    def get(self) -> FakeSnapshot:
        doc = self._store.get(self._doc_id)
        return FakeSnapshot(self._doc_id, doc)

    def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        doc = self._ensure_doc()
        if merge:
            _deep_merge(doc, data)
        else:
            subcollections = doc.get("__subcollections__", {})
            doc.clear()
            doc["__subcollections__"] = subcollections
            _deep_merge(doc, data)

    def update(self, updates: Dict[str, Any]) -> None:
        doc = self._ensure_doc()
        for key, value in updates.items():
            parts = key.split(".")
            target = doc
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = value

    def collection(self, name: str) -> "FakeCollection":
        doc = self._ensure_doc()
        sub_store = doc["__subcollections__"].setdefault(name, {})
        return FakeCollection(sub_store)


class FakeCollection:
    def __init__(self, store: Dict[str, Any]) -> None:
        self._store = store

    def document(self, doc_id: str) -> FakeDocument:
        return FakeDocument(self._store, doc_id)

    def stream(self) -> list[FakeSnapshot]:
        return [FakeSnapshot(doc_id, data) for doc_id, data in self._store.items()]

    def order_by(self, field: str, direction: str | None = None) -> "FakeCollectionView":
        reverse = False
        if direction is not None:
            reverse = str(direction).upper().endswith('DESCENDING')
        return FakeCollectionView(self._store, field, reverse)

class FakeCollectionView:
    def __init__(self, store: Dict[str, Any], field: str, reverse: bool) -> None:
        self._store = store
        self._field = field
        self._reverse = reverse

    def stream(self) -> list[FakeSnapshot]:
        def sort_key(item: tuple[str, Dict[str, Any]]):
            value = item[1].get(self._field)
            return (value is None, value)

        ordered = sorted(self._store.items(), key=sort_key, reverse=self._reverse)
        return [FakeSnapshot(doc_id, data) for doc_id, data in ordered]

class FakeBatch:
    def __init__(self) -> None:
        self._ops: list[Tuple[str, FakeDocument, Dict[str, Any], bool]] = []

    def set(self, doc_ref: FakeDocument, data: Dict[str, Any], merge: bool = False) -> None:
        self._ops.append(("set", doc_ref, data, merge))

    def commit(self) -> None:
        for action, doc_ref, data, merge in self._ops:
            if action == "set":
                doc_ref.set(data, merge=merge)
        self._ops.clear()


class FakeFirestore:
    def __init__(self) -> None:
        self._collections: Dict[str, Dict[str, Any]] = {}

    def collection(self, name: str) -> FakeCollection:
        store = self._collections.setdefault(name, {})
        return FakeCollection(store)

    def batch(self) -> FakeBatch:
        return FakeBatch()

    def get_document_data(self, collection: str, doc_id: str) -> Dict[str, Any]:
        docs = self._collections.get(collection, {})
        snapshot = FakeSnapshot(doc_id, docs.get(doc_id))
        return snapshot.to_dict()

    def get_subcollection_docs(self, collection: str, doc_id: str, subcollection: str) -> Dict[str, Any]:
        docs = self._collections.get(collection, {})
        doc = docs.get(doc_id) or {}
        subcollections = doc.get("__subcollections__", {})
        result: Dict[str, Any] = {}
        for key, value in subcollections.get(subcollection, {}).items():
            cleaned = dict(value)
            cleaned.pop("__subcollections__", None)
            result[key] = cleaned
        return result


class FakeRequest:
    def __init__(self, payload: Dict[str, Any], headers: Dict[str, str] | None = None, args: Dict[str, Any] | None = None) -> None:
        self._payload = payload
        self.headers = headers or {}
        self.auth: Any = None
        self.args = args or {}

    def get_json(self) -> Dict[str, Any]:
        return self._payload


def _extract_status(response: Any) -> int:
    for attr in ("status", "status_code"):
        if hasattr(response, attr):
            return int(getattr(response, attr))
    raise AssertionError("Response missing status attribute")


def _extract_json(response: Any) -> Dict[str, Any]:
    if hasattr(response, "json") and callable(getattr(response, "json")):
        parsed = response.json()
        if isinstance(parsed, dict):
            return parsed
    payload = getattr(response, "response", None)
    if payload is None and hasattr(response, "body"):
        payload = getattr(response, "body")
    if isinstance(payload, (list, tuple)):
        payload = payload[0]
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    if isinstance(payload, str):
        return json.loads(payload)
    if isinstance(payload, dict):
        return payload
    raise AssertionError("Unable to extract JSON payload from response")


@pytest.fixture()
def fake_firestore(monkeypatch: pytest.MonkeyPatch) -> FakeFirestore:
    store = FakeFirestore()
    monkeypatch.setattr(main, "db", store)
    return store


@pytest.fixture()
def model_path_stub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    model_file = tmp_path / "model.dmp"
    model_file.write_bytes(b"stub-model")
    monkeypatch.setattr(main, "_model_path_from_request", lambda _value: model_file)
    return model_file


@pytest.fixture()
def brickplot_stub(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    payload = {
        "image_base64": base64.b64encode(b"demo-image").decode("ascii"),
        "matrix": [[-3.0, -2.5], [-4.1, -3.8]],
        "statistics": {
            "min_energy": -4.1,
            "max_energy": -2.5,
            "mean_energy": -3.35,
            "best_position": {"spacer_config": 1, "sequence_position": 2},
        },
        "sequence": "ATCGATCGAT",
        "sequence_length": 10,
    }
    monkeypatch.setattr(main, "get_brickplot", lambda **_kwargs: payload)
    return payload


def test_submit_job_uploads_fasta(fake_firestore: FakeFirestore, model_path_stub: Path, brickplot_stub: Dict[str, Any]) -> None:
    request = FakeRequest(
        payload={
            "fileContent": FASTA_SEQUENCE_PATH.read_text(),
            "fileName": FASTA_SEQUENCE_PATH.name,
            "jobTitle": "fasta-demo",
            "model": str(model_path_stub),
        },
        headers={"X-Test-Auth": "true", "Authorization": "Bearer token", "X-Test-Provider": "google.com", "X-Test-Email": "user@example.com"},
    )

    response = main.submit_job(request)
    assert _extract_status(response) == 200
    body = _extract_json(response)
    job_id = body["jobId"]
    job_docs = fake_firestore.get_subcollection_docs("users", "test_user_123", "jobhistory")
    assert job_docs[job_id]["jobTitle"] == "fasta-demo"
    assert job_docs[job_id]["sequence"] == FASTA_SEQUENCE
    assert body["brickplot"]["sequence_length"] == brickplot_stub["sequence_length"]


def test_submit_job_success(fake_firestore: FakeFirestore, model_path_stub: Path, brickplot_stub: Dict[str, Any]) -> None:
    main.create_user_document(
        SimpleNamespace(data=SimpleNamespace(uid="test_user_123", email="user@example.com", provider_id="google.com"))
    )

    request = FakeRequest(
        payload={
            "sequence": "ATCGATCGATCG",
            "jobTitle": "demo",
            "predictor": "standard",
            "predictors": {"standard": True},
        },
        headers={"X-Test-Auth": "true", "Authorization": "Bearer token", "X-Test-Provider": "google.com", "X-Test-Email": "user@example.com"},
    )

    response = main.submit_job(request)

    assert _extract_status(response) == 200
    body = _extract_json(response)
    assert body["message"] == "Job completed successfully"
    assert body["brickplot"] == brickplot_stub
    job_id = body["jobId"]

    user_doc = fake_firestore.get_document_data("users", "test_user_123")
    assert user_doc["monthlyUsage"]["count"] == 1
    assert user_doc["authProvider"] == "google.com"
    assert user_doc["firstJob"] == job_id
    assert user_doc["lastJob"] == job_id

    job_docs = fake_firestore.get_subcollection_docs("users", "test_user_123", "jobhistory")
    job_doc = job_docs[job_id]
    assert job_doc["status"] == main.JOB_STATUS["COMPLETED"]
    assert job_doc["nextTitle"] is None
    assert job_doc["predictor"] == "standard"
    assert job_doc["predictors"]["standard"] is True
    assert job_doc["brickplot"] == brickplot_stub


def test_get_job_history_returns_documents(fake_firestore: FakeFirestore, model_path_stub: Path, brickplot_stub: Dict[str, Any]) -> None:
    main.create_user_document(
        SimpleNamespace(data=SimpleNamespace(uid="test_user_123", email="user@example.com", provider_id="google.com"))
    )

    submit_request = FakeRequest(
        payload={
            "sequence": TEXT_SEQUENCE,
            "jobTitle": "history-job",
            "model": str(model_path_stub),
        },
        headers={"X-Test-Auth": "true", "Authorization": "Bearer token", "X-Test-Provider": "google.com", "X-Test-Email": "user@example.com"},
    )
    submit_response = main.submit_job(submit_request)
    assert _extract_status(submit_response) == 200

    history_request = FakeRequest(
        payload={},
        headers={"X-Test-Auth": "true", "Authorization": "Bearer token", "X-Test-Provider": "google.com", "X-Test-Email": "user@example.com"},
        args={"userId": "test_user_123"},
    )
    history_response = main.get_job_history(history_request)
    assert _extract_status(history_response) == 200
    history_body = _extract_json(history_response)
    assert history_body["jobs"]
    assert history_body["jobs"][0]["jobTitle"] == "history-job"


def test_submit_job_appends_linked_list(fake_firestore: FakeFirestore, model_path_stub: Path, brickplot_stub: Dict[str, Any]) -> None:
    main.create_user_document(
        SimpleNamespace(data=SimpleNamespace(uid="test_user_123", email="user@example.com", provider_id="google.com"))
    )

    first_request = FakeRequest(
        payload={
            "sequence": "ATCGATCGATCG",
            "jobTitle": "job-1",
            "predictor": "standard",
            "predictors": {"standard": True},
        },
        headers={"X-Test-Auth": "true", "Authorization": "Bearer t1", "X-Test-Provider": "google.com", "X-Test-Email": "user@example.com"},
    )
    second_request = FakeRequest(
        payload={
            "sequence": "ATCGATCGATCG",
            "jobTitle": "job-2",
            "predictor": "standardSpacer",
            "predictors": {"standardSpacer": True},
        },
        headers={"X-Test-Auth": "true", "Authorization": "Bearer t2", "X-Test-Provider": "google.com", "X-Test-Email": "user@example.com"},
    )

    first_response = main.submit_job(first_request)
    second_response = main.submit_job(second_request)

    job_id_one = _extract_json(first_response)["jobId"]
    job_id_two = _extract_json(second_response)["jobId"]

    user_doc = fake_firestore.get_document_data("users", "test_user_123")
    assert user_doc["firstJob"] == job_id_one
    assert user_doc["lastJob"] == job_id_two
    assert user_doc["monthlyUsage"]["count"] == 2

    job_docs = fake_firestore.get_subcollection_docs("users", "test_user_123", "jobhistory")
    assert job_docs[job_id_one]["nextTitle"] == job_id_two
    assert job_docs[job_id_two]["nextTitle"] is None


def test_submit_job_unauthorized(fake_firestore: FakeFirestore, model_path_stub: Path) -> None:
    request = FakeRequest(payload={})
    response = main.submit_job(request)
    assert _extract_status(response) == 401


def test_submit_job_invalid_sequence(fake_firestore: FakeFirestore, model_path_stub: Path) -> None:
    request = FakeRequest(
        payload={
            "sequence": "ACGT",
        },
        headers={"X-Test-Auth": "true", "Authorization": "Bearer token"},
    )
    response = main.submit_job(request)
    assert _extract_status(response) == 400


def test_submit_job_monthly_limit(fake_firestore: FakeFirestore, model_path_stub: Path) -> None:
    user_doc = fake_firestore.collection("users").document("test_user_123")
    user_doc.set(
        {
            "uid": "test_user_123",
            "monthlyUsage": {"count": 100, "monthYear": datetime_now_month()},
        }
    )

    request = FakeRequest(
        payload={
            "sequence": "ATCGATCGATCG",
            "jobTitle": "demo",
        },
        headers={"X-Test-Auth": "true", "Authorization": "Bearer token"},
    )
    response = main.submit_job(request)
    assert _extract_status(response) == 429


def datetime_now_month() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y-%m")


def test_create_user_document_initialises_firestore(fake_firestore: FakeFirestore) -> None:
    event = SimpleNamespace(
        data=SimpleNamespace(uid="new_user", email="user@example.com", provider_id="google.com")
    )
    response = main.create_user_document(event)
    assert isinstance(response, main.identity_fn.BeforeCreateResponse)

    user_doc = fake_firestore.get_document_data("users", "new_user")
    assert user_doc["uid"] == "new_user"
    assert user_doc["authProvider"] == "google.com"
    assert user_doc["firstJob"] is None
    assert user_doc["lastJob"] is None

    job_docs = fake_firestore.get_subcollection_docs("users", "new_user", "jobhistory")
    placeholder = job_docs["placeholder"]
    assert placeholder["nextTitle"] is None
    assert placeholder["predictor"] is None
    assert set(placeholder["predictors"].keys()) == {"standard", "standardSpacer", "standardSpacerCumulative"}


def test_ping_returns_success() -> None:
    request = SimpleNamespace(headers={})
    response = main.ping(request)  # type: ignore[arg-type]
    assert _extract_status(response) == 200
    body = _extract_json(response)
    assert body["status"] == "success"
