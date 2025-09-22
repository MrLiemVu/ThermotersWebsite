"""Manual trigger helpers for Firebase function entry points."""
from __future__ import annotations

import argparse
import os
os.environ.setdefault('THERMOTERS_FORCE_FIREBASE_ADMIN_STUBS', '1')
os.environ.setdefault('THERMOTERS_FORCE_FUNCTIONS_STUBS', '1')
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

try:
    from functions import main
except ModuleNotFoundError:  # pragma: no cover - allow running from repo root
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from functions import main


class LocalRequest:
    def __init__(self, payload: Dict[str, Any], headers: Dict[str, str] | None = None) -> None:
        self._payload = payload
        self.headers = headers or {}
        self.auth = None
        self.args: Dict[str, Any] = {}

    def get_json(self) -> Dict[str, Any]:
        return self._payload


def _extract_status(response: Any) -> int:
    for attr in ("status", "status_code"):
        if hasattr(response, attr):
            return int(getattr(response, attr))
    return -1


def _extract_body(response: Any) -> Any:
    if hasattr(response, "json") and callable(getattr(response, "json")):
        try:
            return response.json()
        except Exception:  # pragma: no cover - defensive
            pass
    payload = getattr(response, "response", None)
    if payload is None and hasattr(response, "body"):
        payload = getattr(response, "body")
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


def run_submit_job(args: argparse.Namespace) -> None:
    sequence = args.sequence
    payload: Dict[str, Any] = {
        "jobTitle": args.job_title,
        "model": args.model,
        "predictors": {"standard": True},
    }

    if args.sequence_file:
        sequence_path = Path(args.sequence_file)
        if not sequence_path.is_file():
            raise FileNotFoundError(f"Sequence file not found: {sequence_path}")
        content = sequence_path.read_text()
        suffix = sequence_path.suffix.lower()
        if suffix in {".fasta", ".fna", ".ffn", ".faa", ".csv"}:
            payload["fileContent"] = content
            payload["fileName"] = sequence_path.name
        else:
            sequence = content.strip()

    if sequence:
        payload["sequence"] = sequence

    if "sequence" not in payload and "fileContent" not in payload:
        raise ValueError("A sequence or --sequence-file must be provided")
    headers = {"X-Test-Auth": "true", "Authorization": f"Bearer {args.token}"}
    request = LocalRequest(payload, headers=headers)
    response = main.submit_job(request)
    body = _extract_body(response)
    if isinstance(body, dict) and isinstance(body.get("brickplot"), dict):
        brickplot = dict(body["brickplot"])
        image_value = brickplot.get("image_base64")
        if isinstance(image_value, str) and len(image_value) > 50:
            brickplot["image_base64"] = image_value[:50] + "... (truncated)"
        body = dict(body)
        body["brickplot"] = brickplot
    print(f"status={_extract_status(response)}")
    print(json.dumps(body, indent=2, default=str))


def run_get_job_history(args: argparse.Namespace) -> None:
    headers = {"X-Test-Auth": "true", "Authorization": f"Bearer {args.token}"}
    request = LocalRequest({}, headers=headers)
    request.args = {}
    if args.user_id:
        request.args['userId'] = args.user_id
    response = main.get_job_history(request)
    print(f"status={_extract_status(response)}")
    print(json.dumps(_extract_body(response), indent=2, default=str))


def run_create_user(args: argparse.Namespace) -> None:
    event = SimpleNamespace(data=SimpleNamespace(uid=args.uid, email=args.email))
    response = main.create_user_document(event)
    print(f"create_user_document returned: {response.__class__.__name__}")


def run_ping(_: argparse.Namespace) -> None:
    response = main.ping(SimpleNamespace(headers={}))  # type: ignore[arg-type]
    print(f"status={_extract_status(response)}")
    print(json.dumps(_extract_body(response), indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manual triggers for Thermoters Firebase functions")
    sub = parser.add_subparsers(required=True)

    submit = sub.add_parser("submit-job", help="Invoke submit_job locally")
    submit.add_argument("sequence", nargs="?", help="DNA sequence to evaluate")
    submit.add_argument("--sequence-file", help="Path to a sequence file (txt/fasta/csv)")
    submit.add_argument("--job-title", default="manual-test", help="Job title/document id")
    submit.add_argument(
        "--model",
        default=str(main.DEFAULT_MODEL),
        help="Path to the model file (defaults to repository model)",
    )
    submit.add_argument("--token", default="local-test-token", help="Mock bearer token")
    submit.set_defaults(func=run_submit_job)

    history = sub.add_parser("get-job-history", help="Fetch job history for a user")
    history.add_argument("--user-id", help="Target user ID (defaults to the authenticated user)")
    history.add_argument("--token", default="local-test-token", help="Mock bearer token")
    history.set_defaults(func=run_get_job_history)

    user = sub.add_parser("create-user", help="Invoke create_user_document locally")
    user.add_argument("uid", help="UID to seed in Firestore")
    user.add_argument("--email", default="demo@example.com", help="Email address for the new user")
    user.set_defaults(func=run_create_user)

    ping = sub.add_parser("ping", help="Invoke the ping health check")
    ping.set_defaults(func=run_ping)

    return parser


def main_cli() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main_cli()
