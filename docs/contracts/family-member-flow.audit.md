# Cross-Boundary Audit — Family Member Flow (post-build)

**Source:** [docs/contracts/family-member-flow.md](family-member-flow.md)
**Run against:** updated registries at `docs/registries/` + current codebase
**Date:** 2026-05-16 (post-build re-run)

---

## Summary

All 8 punch-list items from the initial audit are complete. Every name in the Feature Contract has both a producer and a consumer, with no shape mismatches. The family-member flow is wired end-to-end pending one operational dependency: **email-link sign-in must be enabled in Firebase Console** (Authentication → Sign-in method → Email/Password → Email link). The invite endpoint surfaces a clear error if it isn't.

---

## Gaps by boundary kind

### Collections

| Collection | Status |
|---|---|
| `family_invitations` | ✓ rule, indexes (×2), producer (invite/revoke/accept endpoints), consumer (accept endpoint) all in place. |
| `care_updates` | ✓ rule, index, producer (`client.html` postCareUpdate), consumers (`client.html` + `family.html`) all in place. |
| `users` (role="family" extension) | ✓ accept-invite writes `role`, `family_group_ids`, `relationship_to_parent` to the user doc. Existing self/admin rule covers reads and writes. |
| `family_messages` | ✓ rule in place. Producer (family.html) exists; practitioner-side reader not built yet — flagged as orphan consumer side, not blocking. |
| `family_groups` read rule | ✓ now uses `inFamilyGroups()` helper that checks array membership in `family_group_ids` claim. |
| `parents`, `medications`, `care_plans`, `crisis_info` reads | ✓ all routed through `canAccessFamilyData()` which uses the array helper. |

### Claims

| Claim | Status |
|---|---|
| `family` | ✓ set by `/auth/accept-invite`. Checked in 4 client pages and across rules. |
| `family_group_ids` (array) | ✓ set/appended by accept-invite; mutated by revoke endpoint. Read by `family.html`. Used by rules via `inFamilyGroups()`. `family.html` keeps a legacy fallback read of singular `family_group_id` for any user provisioned before the array. |
| `family_group_id` (singular) | retired from rules; kept only as a defensive fallback in `family.html`. |
| `profession`, `beta` | still orphan producers — set by signup but never read. Not blocking the family flow. |
| `relationship_to_parent` | stored on user doc only (intentional — not gating anything). |

### Endpoints

| Endpoint | Status |
|---|---|
| `POST /family-groups/{id}/invite` | ✓ implemented. Verifies ownership, creates/refreshes `family_invitations`, generates Firebase email-link, sends via Brevo. |
| `POST /family-groups/{id}/revoke` | ✓ implemented. Removes group id from `family_group_ids` claim, revokes refresh tokens, marks invitation revoked. **Orphan caller** — no UI calls it yet. To be wired when a manage-family-members page is built. |
| `POST /auth/accept-invite` | ✓ implemented. Matches pending invitations by signed-in email, sets claims, writes user doc. |
| `POST /ai/ask` | ✓ reachable by family role via `require_auth`. |
| `POST /ai/intake` | ⚠ still missing (unchanged — separate from family flow). |

### Pages (UI promises)

| Page / UI | Status |
|---|---|
| `/accept-invite.html` | ✓ built. Handles Firebase email-link signin, prompts for email re-confirmation on cross-device flows, calls accept-invite, redirects to `/family.html`. |
| `family.html` group switcher | ✓ added. Hidden when only one group; dropdown when multiple. Persists selection in localStorage. |
| `client.html` care updates producer UI | ✓ new "Care Updates" tab with composer + recent-updates list. |
| `family.html` care updates feed | ✓ "Recent updates" section near the top of the dashboard. |
| `new-client.html` invite UI | ✓ existing — now reaches a working endpoint. |

### Indexes

| Index | Status |
|---|---|
| `family_invitations(invited_email, status)` | ✓ |
| `family_invitations(family_group_id, invited_at DESC)` | ✓ |
| `care_updates(family_group_id, posted_at DESC)` | ✓ |

---

## Operational dependency (not a code gap)

**Firebase Console — enable Email link (passwordless sign-in)**
The invite endpoint's call to `generate_sign_in_with_email_link()` requires this setting. Path: Firebase Console → Authentication → Sign-in method → Email/Password → enable "Email link (passwordless sign-in)". The endpoint returns a clear error message if it's not enabled, so the practitioner gets actionable feedback if the setup step is missed.

---

## Adjacent items still on the project punch list (out of scope for this contract)

- `/ai/intake` endpoint missing (called by `intake.html:548`).
- `api/routers/session_notes.py` still targets the wrong subcollection path.
- `intake_data` orphan producer.
- `profession` / `beta` claims orphan producers.
- `aiConversations` rule exists but no code path.
- Practitioner-side family_messages reader UI not built.
- Manage-family-members page not built (would consume `/family-groups/{id}/revoke`).

---

## What to test

1. Practitioner signs in, creates a new client with an invite email, posts a care update.
2. Family member opens email, clicks link, lands on `/accept-invite.html`, confirms email if prompted, lands on `/family.html` and sees the parent info, medications, care plan summary, and care update.
3. Same family member is invited to a second family group — the group switcher appears in the nav and switching reloads data.
4. Practitioner re-invites the same email — the existing pending invitation is refreshed instead of duplicated.
5. (Optional, no UI yet) Hit `POST /family-groups/{id}/revoke` directly with a UID; family user's next request fails until they re-sign in.

If step 1's email never arrives, check Firebase Console (email-link signin enabled) and Brevo logs.
