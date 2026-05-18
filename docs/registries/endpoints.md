# API Endpoint Registry

Every HTTP endpoint served by `api/` and every place in the client that calls one. For each endpoint: route, served by, callers, auth requirement, request/response shape, and any mismatches.

Update this file whenever an endpoint is added, removed, or its shape changes.

Base URL (production): `https://careguide-api-658340465706.us-central1.run.app` (service: `careguide-api`)
Base URL (stage):      `https://careguide-api-stage-658340465706.us-central1.run.app` (service: `careguide-api-stage`)

Browser pages pick automatically via `js/api-base.js` based on `window.location.hostname` (`stage.` prefix → stage; else prod).

---

## Users

### `POST /users/register`
**Served by:** `api/routers/users.py:42`
**Auth:** `require_auth` (Firebase ID token)
**Callers:** `signup.html:848`
**Request:** `{full_name, profession, license_states[], beta?}`
**Response:** `{success, uid, role, profession, beta}`
**Side effects:** sets `practitioner` claim; writes `users/{uid}` doc with `status: pending_activation` (including `profession` and `beta` fields, which are data, not claims); sends welcome email via Brevo.
**Status:** ✓

### `POST /users/{uid}/status`
**Served by:** `api/routers/users.py:229`
**Auth:** `require_admin`
**Callers:** `admin-approvals.html:442`
**Request:** `{status: "active" | "rejected"}`
**Response:** `{success, uid, status}`
**Side effects:** updates `users/{uid}.status` + timestamp; sets or clears claims; sends approval/rejection email.
**Status:** ✓

---

## Auth Verification

### `POST /auth/send-verification`
**Served by:** `api/routers/auth_verification.py:60`
**Auth:** `require_auth`
**Callers:** `signup.html:860` (post-register auto-send); `dashboard.html:633` (resend-verification button for unverified practitioners)
**Request:** none
**Response:** `{success, email}` or `{success, already_verified: true}`
**Side effects:** creates token in `email_verification_tokens`; sends Brevo email.
**Status:** ✓

### `POST /auth/verify-email?token=...`
**Served by:** `api/routers/auth_verification.py:128`
**Auth:** none (token is the credential)
**Callers:** `verify-email.html:187`
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
**Served by:** `api/routers/family_groups.py` invite_family_member
**Auth:** `require_practitioner` (must own the target family_group)
**Callers:** `new-client.html:783`
**Request:** `{email, relationship}`
**Response:** `{success, invitation_id, email_sent}`
**Side effects:** creates / refreshes a `family_invitations` doc; generates a Firebase email-link sign-in URL via Admin SDK; sends via Brevo. Requires Firebase Console: Authentication → Sign-in method → Email/Password → Email link (passwordless sign-in) enabled.
**Status:** ✓

### `POST /family-groups/{group_id}/revoke`
**Served by:** `api/routers/family_groups.py` revoke_family_member
**Auth:** `require_practitioner` (must own the target family_group)
**Callers:** `client.html` revokeFamilyMember (Family Members tab)
**Request:** `{uid}`
**Response:** `{success, uid, revoked, remaining_groups}`
**Side effects:** removes the group_id from the target user's `family_group_ids` claim; revokes refresh tokens; updates the user doc; marks any associated `family_invitations` records as revoked.
**Status:** ✓

### `POST /auth/accept-invite`
**Served by:** `api/routers/auth_verification.py` accept_invite
**Auth:** `require_auth` (Firebase ID token from email-link sign-in)
**Callers:** `accept-invite.html`
**Request:** none (uses signed-in user's email)
**Response:** `{success, accepted, family_group_ids}`
**Side effects:** looks up pending `family_invitations` by the signed-in user's email; appends each group's id to `family_group_ids` claim; sets `family: true` claim; writes/merges users doc with `role: "family"`; marks invitations accepted.
**Status:** ✓

---

## Parents

### `POST /parents/`
**Served by:** `api/routers/parents.py`
**Auth:** `require_practitioner` (must own the target `family_group`)
**Callers:** none (client uses direct Firestore write)
**Request:** `{family_group_id, first_name, last_name, care_level?, dob?, state?, invite_email?}`
**Response:** `{id, ...parent fields}`
**Status:** ⚠ orphan — endpoint is correct, but no client caller. Direct Firestore write from `new-client.html:773` is the live path.

### `GET /parents/?family_group_id=...`
**Served by:** `api/routers/parents.py`
**Callers:** none
**Status:** ⚠ orphan.

### `GET /parents/{parent_id}`, `PATCH /parents/{parent_id}`, `DELETE /parents/{parent_id}`
**Served by:** `api/routers/parents.py`
**Auth:** `require_practitioner` (must own the parent's family group)
**Callers:** none
**Status:** ⚠ orphan.

---

## Medications

### `POST /medications/`
**Served by:** `api/routers/medications.py`
**Auth:** `require_practitioner` (must own the target `family_group`)
**Callers:** none (client uses direct Firestore write)
**Request:** `{family_group_id, name, dosage?, frequency?, prescriber?, start_date?, status?, notes?}`
**Response:** `{id, ...medication fields}`
**Status:** ⚠ orphan — endpoint is correct, but no client caller. Direct Firestore writes from `medications.html` are the live path.

### `GET /medications/?family_group_id=...`
**Served by:** `api/routers/medications.py`
**Callers:** none
**Status:** ⚠ orphan.

### `GET /medications/{med_id}`, `PATCH /medications/{med_id}`, `DELETE /medications/{med_id}`
**Served by:** `api/routers/medications.py`
**Auth:** `require_practitioner` (must own the med's family group)
**Callers:** none
**Status:** ⚠ orphan.

---

## Session Notes

### `POST /session-notes/`
**Served by:** `api/routers/session_notes.py` create_session_note
**Auth:** `require_practitioner` (must own the target family_group)
**Callers:** none (client uses direct Firestore write)
**Request:** `{family_group_id, type?, text, billable_minutes?}`
**Response:** `{id, ...note fields}`
**Status:** ⚠ orphan — endpoint is correct, no client caller.

### `GET /session-notes/?family_group_id=...`
**Served by:** `api/routers/session_notes.py` list_session_notes
**Callers:** none
**Status:** ⚠ orphan.

### `GET /session-notes/{id}`, `PATCH /session-notes/{id}`, `DELETE /session-notes/{id}`
**Served by:** `api/routers/session_notes.py`
**Auth:** `require_practitioner` (must own the note's family group)
**Callers:** none
**Status:** ⚠ orphan.

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

### `POST /ai/intake`
**Served by:** `api/routers/ai.py`
**Auth:** `require_practitioner` (must own the target `family_group`)
**Callers:** `intake.html:549`
**Request:** `{family_group_id: str, intake: dict}`
**Response:** `{sections: {situation, goals, interventions, family_role, barriers, next_steps}, intake_summary: str}`
**Side effects:** verifies ownership of `family_groups/{family_group_id}`; writes `intake_data/{family_group_id}` via Admin SDK (merge) with the caller's `practitioner_id` and the raw intake; calls Claude to map the intake into the six care-plan sections plus a short synthesis paragraph.
**Status:** ✓

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
**Callers:** `contact.html:434`
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
| POST /family-groups/{id}/invite         | ✓      | ✓      | OK                        |
| POST /family-groups/{id}/revoke         | ✓      | ✓      | OK                        |
| POST /auth/accept-invite                | ✓      | ✓      | OK                        |
| POST /ai/intake                         | ✓      | ✓      | OK                        |
| GET/POST/GET /family-groups/...         | ✓      | ✗      | orphan (correct schema)   |
| /parents/ (CRUD)                        | ✓      | ✗      | orphan (client uses direct Firestore) |
| /medications/ (CRUD)                    | ✓      | ✗      | orphan (client uses direct Firestore) |
| POST/GET/PATCH/DELETE /session-notes/...| ✓      | ✗      | orphan (correct schema)   |
| POST /ai/care-plan-draft, /session-note-draft, /ask | ✓ | ✗ | ⚠ orphan (planned) |
| POST /notifications/email, /sms, /reminder | ✓   | ✗      | ⚠ orphan                  |
