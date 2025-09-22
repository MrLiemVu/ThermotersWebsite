"""Minimal firebase_admin stubs for local unit tests and CLI helpers."""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, Iterable, Optional

_firestore_store: Dict[str, Dict[str, Any]] = {}
_app: Optional[object] = None


class _FakeSnapshot:
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]) -> None:
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> Dict[str, Any]:
        if not self._data:
            return {}
        data = dict(self._data)
        data.pop("__subcollections__", None)
        return data

class _FakeDocument:
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

    def get(self) -> _FakeSnapshot:
        return _FakeSnapshot(self._doc_id, self._store.get(self._doc_id))

    def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        doc = self._ensure_doc()
        if merge:
            _deep_merge(doc, data)
        else:
            sub = doc.get("__subcollections__", {})
            doc.clear()
            doc["__subcollections__"] = sub
            _deep_merge(doc, data)

    def update(self, updates: Dict[str, Any]) -> None:
        doc = self._ensure_doc()
        for key, value in updates.items():
            parts = key.split(".")
            target = doc
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = value

    def collection(self, name: str) -> "_FakeCollection":
        sub_store = self._ensure_doc()["__subcollections__"].setdefault(name, {})
        return _FakeCollection(sub_store)


class _FakeCollection:
    def __init__(self, store: Dict[str, Any]) -> None:
        self._store = store

    def document(self, doc_id: str) -> _FakeDocument:
        return _FakeDocument(self._store, doc_id)

    def stream(self) -> Iterable[_FakeSnapshot]:
        return [_FakeSnapshot(doc_id, data) for doc_id, data in self._store.items()]

    def order_by(self, field: str, direction: Any = None) -> "_FakeCollectionView":
        reverse = False
        if direction is not None:
            reverse = str(direction).upper().endswith('DESCENDING')
        return _FakeCollectionView(self._store, field, reverse)

class _FakeCollectionView:
    def __init__(self, store: Dict[str, Any], field: str, reverse: bool) -> None:
        self._store = store
        self._field = field
        self._reverse = reverse

    def stream(self) -> Iterable[_FakeSnapshot]:
        def sort_key(item: tuple[str, Dict[str, Any]]):
            value = item[1].get(self._field)
            if isinstance(value, datetime):
                return value
            return (value is None, value)

        ordered = sorted(self._store.items(), key=sort_key, reverse=self._reverse)
        return [_FakeSnapshot(doc_id, data) for doc_id, data in ordered]

class _FakeBatch:
    def __init__(self, client: "_FakeFirestore") -> None:
        self._client = client
        self._ops: list[tuple[str, _FakeDocument, Dict[str, Any], bool]] = []

    def set(self, doc_ref: _FakeDocument, data: Dict[str, Any], merge: bool = False) -> None:
        self._ops.append(("set", doc_ref, data, merge))

    def commit(self) -> None:
        for action, doc_ref, data, merge in self._ops:
            if action == "set":
                doc_ref.set(data, merge=merge)
        self._ops.clear()


class _FakeFirestore:
    def __init__(self, store: Dict[str, Dict[str, Any]]) -> None:
        self._store = store

    def collection(self, name: str) -> _FakeCollection:
        collection_store = self._store.setdefault(name, {})
        return _FakeCollection(collection_store)

    def batch(self) -> _FakeBatch:
        return _FakeBatch(self)


def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    for key, value in source.items():
        if key == "__subcollections__":
            continue
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


def initialize_app(credential: Any | None = None) -> object:
    global _app
    _app = object()
    return _app


def get_app() -> object:
    if _app is None:
        raise ValueError("The default Firebase app does not exist.")
    return _app


def client(app: object) -> _FakeFirestore:
    return _FakeFirestore(_firestore_store)


class _CredentialsModule:
    class Certificate:
        def __init__(self, path: str) -> None:
            self.path = path


credentials = _CredentialsModule()
firestore = SimpleNamespace(client=client)

__all__ = [
    "initialize_app",
    "get_app",
    "credentials",
    "firestore",
]
