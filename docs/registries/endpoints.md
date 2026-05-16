# API Endpoint Registry

Every HTTP endpoint served by `api/` and every place in the client that calls one. For each endpoint: route, served by, callers, auth requirement, request/response shape, and any mismatches.

Update this file whenever an endpoint is added, removed, or its shape changes.

Base URL (production): `https://careguide-api-658340465706.us-central1.run.app`

---

## Users

### `POST /users/register`
**Served by:** `api/routers/users.py:42`
**Auth:** `require_auth` (Firebase ID token)
**Callers:** `signup.html:847`
**Request:** `{full_name, profession, license_states[], beta?}`
**Response:** `{success, uid, role, profession, beta}`
**Side effects:** sets `practitioner`/`profession`/`beta` claims; writes `users/{uid}` doc with `status: pending_activation`; sends welcome email via Brevo.
**Status:** ✓

### `POST /users/{uid}/status`
**Served by:** `api/routers/users.py:229`
**Auth:** `require_admin`
**Callers:** `admin-approvals.html:441`
**Request:** `{status: "active" | "rejected"}`
**Response:** `{success, uid, status}`
**Side effects:** updates `users/{uid}.status` + timestamp; sets or clears claims; sends approval/rejection email.
**Status:** ✓

---

## Auth Verification

### `POST /auth/send-verification`
**Served by:** `api/routers/auth_verification.py:60`
**Auth:** `require_auth`
**Callers:** `signup.html:859`
**Request:** none
**Response:** `{success, email}` or `{success, already_verified: true}`
**Side effects:** creates token in `email_verification_tokens`; sends Brevo email.
**Status:** ✓

### `POST /auth/verify-email?token=...`
**Served by:** `api/routers/auth_verification.py:128`
**Auth:** none (token is the credential)
**Callers:** `verify-email.html:186`
**Request:** `?token=` query param
**Response:** `{success, uid}`
**Side effects:** marks Firebase Auth `email_verified=true`; deletes token.
**Status:** ✓

---

## Family Groups

### `GET /family-groups/`
**Served by:** `api/routers/family_groups.py:21`
**Auth:** `require_practitioner`
**Callers:** none
**Status:** ⚠ orphan — no caller, but correctly reads top-level `family_groups`. Available when the client switches to API-mediated reads.

### `POST /family-groups/`
**Served by:** `api/routers/family_groups.py:30`
**Callers:** none
**Status:** ⚠ orphan — correctly writes top-level `family_groups`.

### `GET /family-groups/{group_id}`
**Served by:** `api/routers/family_groups.py:49`
**Callers:** none
**Status:** ⚠ orphan — correctly reads top-level `family_groups` with ownership check.

### `POST /family-groups/{group_id}/invite`
**Served by:** `api/routers/family_groups.py:62` (stub)
**Callers:** `new-client.html:779`
**Status:** ⚠ **501 Not Implemented** — endpoint exists and explicitly returns 501. `new-client.html` now surfaces the failure to the practitioner via a toast on landing instead of silently dropping. Full invite/accept flow tracked in [docs/registries/claims.md](claims.md) (missing `family` and `family_group_id` setters).

---

## Parents

### `POST /parents/`
**Served by:** `api/routers/parents.py:31`
**Callers:** none (client uses direct Firestore write)
**Status:** ⚠ orphan — correctly writes top-level `parents` with ownership check. Available when client switches to API-mediated writes.

### `GET /parents/{group_id}`
**Served by:** `api/routers/parents.py:54`
**Callers:** none
**Status:** ⚠ orphan — correctly reads top-level `parents` filtered by `family_group_id`.

---

## Medications

### `POST /medications/`
**Served by:** `api/routers/medications.py:30`
**Callers:** none (client uses direct Firestore write)
**Status:** ⚠ orphan — correctly writes top-level `medications` with ownership check.

### `GET /medications/{group_id}`
**Served by:** `api/routers/medications.py:53`
**Callers:** none
**Status:** ⚠ orphan — correctly reads top-level `medications` ordered by `created_at` desc.

---

## Session Notes

### `POST /session-notes/`
**Served by:** `api/routers/session_notes.py:13`
**Callers:** none (client uses direct Firestore write)
**Status:** ⚠ orphan + wrong path (`practitioners/{uid}/sessionNotes` subcollection).

### `GET /session-notes/`
**Served by:** `api/routers/session_notes.py:28`
**Callers:** none
**Status:** ⚠ orphan + wrong path.

---

## AI

### `POST /ai/care-plan-draft`
**Served by:** `api/routers/ai.py:15`
**Auth:** `require_practitioner`
**Callers:** none currently
**Request:** `{transcript}` → **Response:** `{draft}`
**Status:** ⚠ orphan — wired for future use.

### `POST /ai/session-note-draft`
**Served by:** `api/routers/ai.py:19`
**Callers:** none currently
**Status:** ⚠ orphan.

### `POST /ai/ask`
**Served by:** `api/routers/ai.py:23`
**Auth:** `require_auth`
**Callers:** none currently
**Status:** ⚠ orphan.

### `POST /ai/intake` ⚠ MISSING
**Served by:** none
**Callers:** `intake.html:548`
**Request:** `{family_group_id, intake}` → **Response (expected):** `{sections}` or `{care_plan}`
**Status:** ⚠ **CRITICAL** — caller exists, endpoint not implemented. The whole intake → AI care plan flow on `intake.html` is broken.

---

## Notifications

### `POST /notifications/email`
**Served by:** `api/routers/notifications.py:36`
**Callers:** none currently
**Status:** ⚠ orphan — internal helper, may be called server-side only.

### `POST /notifications/sms`
**Served by:** `api/routers/notifications.py:53`
**Callers:** none
**Status:** ⚠ orphan.

### `POST /notifications/reminder`
**Served by:** `api/routers/notifications.py:64`
**Callers:** none
**Status:** ⚠ orphan.

---

## Other

### `POST /contact`
**Served by:** `api/routers/contact.py:28`
**Auth:** none
**Callers:** `contact.html:433`
**Status:** ✓

### `GET /health`
**Served by:** `api/routers/health.py:5`
**Callers:** uptime checks only.
**Status:** ✓

---

## Summary

| Endpoint                                | Served | Called | Status                    |
|-----------------------------------------|--------|--------|---------------------------|
| POST /users/register                    | ✓      | ✓      | OK                        |
| POST /users/{uid}/status                | ✓      | ✓      | OK                        |
| POST /auth/send-verification            | ✓      | ✓      | OK                        |
| POST /auth/verify-email                 | ✓      | ✓      | OK                        |
| POST /contact                           | ✓      | ✓      | OK                        |
| GET  /health                            | ✓      | ✓      | OK                        |
| POST /family-groups/{id}/invite         | stub (501) | ✓ | ⚠ not implemented, but surfaces |
| POST /ai/intake                         | ✗      | ✓      | ⚠ missing endpoint        |
| GET/POST/GET /family-groups/...         | ✓      | ✗      | orphan (correct schema)   |
| POST/GET /parents/...                   | ✓      | ✗      | orphan (correct schema)   |
| POST/GET /medications/...               | ✓      | ✗      | orphan (correct schema)   |
| POST/GET /session-notes/...             | ✓ (broken) | ✗ | ⚠ orphan + wrong collection |
| POST /ai/care-plan-draft, /session-note-draft, /ask | ✓ | ✗ | ⚠ orphan (planned) |
| POST /notifications/email, /sms, /reminder | ✓   | ✗      | ⚠ orphan                  |
