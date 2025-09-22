"""Minimal firebase_functions stubs for local testing without the real dependency."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional


@dataclass
class _Response:
    status: int
    headers: Dict[str, str]
    response: Optional[Any] = None

    def json(self) -> Any:
        """Best-effort JSON parsing helper to match the real API signature."""
        if self.response is None:
            return None
        payload = self.response
        if isinstance(payload, (list, tuple)):
            payload = payload[0]
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                return payload
        return payload


def _identity_decorator(*_args: Any, **_kwargs: Any) -> Callable:
    def decorator(func: Callable) -> Callable:
        return func
    return decorator


class _HttpsFn:
    Response = _Response
    Request = object  # Placeholder for typing only

    @staticmethod
    def on_request(**_kwargs: Any) -> Callable:
        return _identity_decorator(**_kwargs)


https_fn = _HttpsFn()


class _FirestoreFn:
    pass


firestore_fn = _FirestoreFn()


class _BeforeCreateResponse:
    """Simple stand-in for Firebase BeforeCreateResponse."""
    def __init__(self) -> None:
        self.ok = True


class _AuthBlockingEvent:
    def __init__(self, data: Any) -> None:
        self.data = data


class _IdentityFn:
    BeforeCreateResponse = _BeforeCreateResponse
    AuthBlockingEvent = _AuthBlockingEvent

    @staticmethod
    def before_user_created(**_kwargs: Any) -> Callable:
        return _identity_decorator(**_kwargs)


identity_fn = _IdentityFn()

__all__ = ["https_fn", "firestore_fn", "identity_fn"]
