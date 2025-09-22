# Thermoters Firebase Functions

Backend for the Thermoters gene expression prediction platform implemented with Firebase Functions (2nd generation) and Python.

## Data Flow Overview

### Account Provisioning

```text
[Client] -- Google Sign-In --> [Firebase Auth]
    |                                |
    |            before_user_created  v
    +-------> [create_user_document] -----> Firestore
                          |                users/{uid}
                          |                +- authProvider = google.com
                          |                +- createdAt, lastLogin timestamps
                          |                +- firstJob = null, lastJob = null
                          |                +- monthlyUsage { count = 0, monthYear }
                          |                +- jobhistory/placeholder (seed doc)
```

The seed `jobhistory/placeholder` document contains all required fields (`brickplot`, `jobTitle`, `nextTitle`, `predictor`, `predictors.*`, `sequence`, `status`, `uid`, `uploadedAt`) with neutral defaults so downstream tooling always sees the expected schema.

### Job Submission / Linked-List History

```text
[Client] -- submit_job request --> [Cloud Function]
    |                                  |
    |  validate payload + quotas        v
    |                             Firestore (users/{uid})
    |                                  |
    |                       update monthlyUsage.count
    |                       append jobhistory/{jobId}
    |                           +- predictor & predictors.*
    |                           +- jobTitle, sequence
    |                           +- nextTitle = null
    |                           +- status = processing
    |                           +- uploadedAt timestamp
    |                                  |
    |<------------- brickplot data -----+
```

Each new job document is assigned a unique `jobId`. The user document is updated so `firstJob` keeps the oldest job id, `lastJob` the most recent. The previously newest job receives its `nextTitle` pointer, giving you a singly linked list that makes archival sweeps trivial.

Re-running a job is as simple as sending the same payload again—`submit_job` records a brand-new history node with identical fields and the link chain stays intact.

## Firestore Schema (enforced by functions)

### `users/{uid}`
- `uid`: string (copied from Auth)
- `email`: string | null
- `authProvider`: string (e.g. `google.com`, defaults to `unknown` only if the upstream event omits it)
- `createdAt`, `lastLogin`: ISO timestamps
- `firstJob`, `lastJob`: string | null (head/tail of the job linked list)
- `monthlyUsage`: `{ count: int, monthYear: YYYY-MM }`

### `users/{uid}/jobhistory/{jobId}`
- `uid`: string (owner)
- `jobTitle`: string (human label)
- `predictor`: string (primary predictor used for the run)
- `predictors`: `{ standard: bool, standardSpacer: bool, standardSpacerCumulative: bool }`
- `sequence`: string (input sequence)
- `brickplot`: null while running; replaced with the result payload (matrix + base64 image) after completion
- `status`: `processing | completed | error | placeholder`
- `nextTitle`: string | null (forward link in the history chain)
- `uploadedAt`: timestamp (job creation time)
- Additional fields captured for reproducibility: `plusOne`, `rc`, `prefixSuffix`, `maxValue`, `minValue`, `threshold`

## Implementation Notes

- `create_user_document` (Auth blocking trigger) now delegates to `_build_user_profile` to populate the required user properties and seeds the placeholder history document.
- `submit_job` normalizes the predictor flags, generates unique job ids, maintains the linked list pointers (`firstJob`, `lastJob`, `nextTitle`), and persists brickplot output back onto the job document after rendering.
- Local stubs under `_stubs/` allow the module to run without Firebase SDKs when executing tests.

## Testing

Run the suite from the `functions` directory:

```bash
python -m pytest
```

Key coverage:
- `tests/test_submit_job.py::test_create_user_document_initialises_firestore` checks the seeded user + placeholder job schema.
- `tests/test_submit_job.py::test_submit_job_success` verifies a full job lifecycle (Firestore writes, schema, returned brickplot payload).
- `tests/test_submit_job.py::test_submit_job_appends_linked_list` proves the linked-list metadata (`firstJob`, `lastJob`, `nextTitle`) updates correctly across successive submissions.
- `tests/test_brickplot.py` exercises the `BrickPlotter` class, confirming a non-empty matrix/image is produced and offering an optional `run_demo()` helper to render the plot via `matplotlib.imshow`.

All tests currently pass (`python -m pytest`), and lint-friendly docstrings/comments highlight the non-obvious linkage logic inside the handlers without cluttering the codebase.

## Manual Trigger Helpers

For ad-hoc verification without deploying:
- `python tests/run_manual_triggers.py create-user demo_uid --email demo@example.com`
- `python tests/run_manual_triggers.py submit-job ATCGATCGATCG --job-title demo`

These helpers use the same code paths and Preserve the Firestore schema described above, so you can watch documents materialise in the emulator or live project while you validate the front-end wiring.
