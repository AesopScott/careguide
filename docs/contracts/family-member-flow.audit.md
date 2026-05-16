# Cross-Boundary Audit — Family Member Flow

**Source:** [docs/contracts/family-member-flow.md](family-member-flow.md)
**Run against:** existing registries at `docs/registries/` + current codebase
**Date:** 2026-05-16

---

## Summary

The contract introduces **2 new collections**, **2 new claims** (one replacing a deferred singular form), **3 new API endpoints** (one currently a 501 stub), **1 new page**, and **rule changes on 5 existing collections** to switch from a singular family_group_id check to array membership.

Nothing in the contract is internally inconsistent. Every name has a planned producer and a planned consumer. The audit's job here is to enumerate what doesn't yet exist so it becomes a build punch list.

---

## Gaps by boundary kind

### Collections (`docs/registries/collections.md`)

| Collection | Status | Needed for |
|---|---|---|
| `family_invitations` | ⚠ does not exist (no rule, no producer, no consumer) | every invite |
| `care_updates` | ⚠ does not exist (no rule, no producer, no consumer) | care updates feed |
| `users` (role="family" extension) | ⚠ existing rule covers reads/writes, but the role="family" path has never been exercised; new fields `relationship_to_parent` and `family_group_ids` (array) are not currently written | every family-member profile |
| `family_messages` | ✓ rule already in place | already wired |
| `family_groups` read rule | ⚠ today uses singular `family_group_id` claim — must switch to array membership | family read access |
| `parents` read rule | ⚠ same — `canAccessFamilyData()` helper uses singular | family read access |
| `medications` read rule | ⚠ same | family read access |
| `care_plans` read rule | ⚠ same | family read access |
| `crisis_info` read rule | ⚠ same | family read access |

### Claims (`docs/registries/claims.md`)

| Claim | Status |
|---|---|
| `family` | ⚠ consumer-only today (checked in 4 places, never set). Needs setter in `/auth/accept-invite`. |
| `family_group_ids` (array) | ⚠ doesn't exist yet. Replaces the singular `family_group_id` placeholder in the existing claims registry. Needs setter on accept; needs mutator on revoke. |
| `family_group_id` (singular) | ⚠ retire — references in `firestore.rules` and `family.html:375` need to change to array membership. |
| `relationship_to_parent` | ✓ stored in Firestore only, no token gating — no claim needed. |

### Endpoints (`docs/registries/endpoints.md`)

| Endpoint | Status |
|---|---|
| `POST /family-groups/{id}/invite` | ⚠ currently a 501 stub. Needs implementation: write `family_invitations` doc, call Firebase Admin `generate_sign_in_with_email_link()`, send via Brevo. |
| `POST /auth/accept-invite` | ⚠ does not exist. Validates Firebase email-link signin, looks up matching pending invitation, sets/appends claims, writes user doc, marks invitation accepted. |
| `POST /family-groups/{id}/revoke` | ⚠ does not exist. Removes a family_group_id from the user's array claim and revokes refresh tokens. |
| `POST /ai/ask` | ✓ exists; reachable by family role once they have an authenticated session. |

### Pages (UI promises)

| Page / UI | Status |
|---|---|
| `/accept-invite.html` | ⚠ does not exist. New page. |
| `family.html` group switcher | ⚠ family.html exists but assumes single `family_group_id` claim. Needs to read array and render a switcher (or "pick a family" landing) when more than one. |
| `client.html` care updates producer UI | ⚠ does not exist. Needs a compose box that writes to `care_updates`. |
| `family.html` care updates feed | ⚠ does not exist. Needs a feed component reading `care_updates` ordered by `posted_at desc`. |
| `new-client.html` invite UI | ✓ exists (already plumbed to the invite endpoint stub). Once the endpoint works, this works. |

### Indexes (`firestore.indexes.json`)

| Collection / query | Status |
|---|---|
| `family_invitations` where `invited_email == X` and `status == 'pending'` (accept lookup) | ⚠ composite index needed. |
| `family_invitations` where `family_group_id == X` orderBy `invited_at desc` (practitioner-side list) | ⚠ composite index needed. |
| `care_updates` where `family_group_id == X` orderBy `posted_at desc` (feed) | ⚠ composite index needed. |

---

## Build punch list (each item ≈ one PR)

Listed in the order the build should happen so each step unblocks the next.

1. **Rules + indexes update.** In `firestore.rules`: rename `family_group_id` claim check to `family_group_ids` array-membership across `/family_groups`, `canAccessFamilyData()`, `/care_plans`, `/crisis_info`. Add rules for `/family_invitations` (practitioner CRUD for owned groups; admin full; family no direct access) and `/care_updates` (practitioner CRUD for owned groups; family read; admin full). In `firestore.indexes.json`: add the three composite indexes listed above.

2. **`POST /family-groups/{id}/invite` implementation.** Replace the 501 stub. Verify group ownership, validate email, create `family_invitations` doc, generate Firebase email-link via Admin SDK, send via Brevo. Return `{success, invitation_id}`. Surface 4xx for duplicate-pending invites or invalid email.

3. **`POST /auth/accept-invite` endpoint.** Require auth. Look up pending invitations matching `request.auth.token.email`. For each match: append `family_group_id` to user's `family_group_ids` claim, set `family: true` claim, write/merge users doc with `role: "family"`, `family_group_ids`, `relationship_to_parent`, mark invitation accepted with timestamp. Return list of accepted group ids.

4. **`/accept-invite.html` page.** Built on Firebase's email-link signin flow: detect link, prompt for email confirmation (Firebase requirement), `signInWithEmailLink`, then call `/auth/accept-invite`, redirect to `/family.html`.

5. **`family.html` multi-group support.** Read the array claim, render a group switcher in the header (or a landing screen if multiple groups). Existing single-group logic becomes the special case.

6. **Care updates UI.** Producer on `client.html` (a "Post update" composer writing to `care_updates`). Consumer feed on `family.html` (newest-first list ordered by `posted_at`).

7. **`POST /family-groups/{id}/revoke` endpoint.** Verify group ownership, remove `family_group_id` from target user's array claim, `revoke_refresh_tokens(uid)`. Update `family_invitations` status to revoked.

8. **Registry updates.** After each PR ships, update `docs/registries/collections.md`, `claims.md`, `endpoints.md` in the same commit. Re-run `/cross-boundary-audit` once the flow is end-to-end to verify reality matches the contract.

---

## What's NOT a gap

- `family_messages` rule — already in place from earlier audit work. ✓
- `users` collection access for family role — already covered by the self-or-admin rule. ✓
- `POST /ai/ask` — already exists, `require_auth` covers family role. ✓
- The `crisis_info` and `care_plans` access patterns — rules already let family read; only the claim-shape change is needed.

---

## Adjacent items surfaced (not blocking family flow but worth flagging)

- `intake_data` is still an orphan producer (written by `intake.html`, never read). The family contract doesn't fix this — it's a separate item still on the project punch list.
- `/ai/intake` endpoint is still missing (called by `intake.html:548`). Separate from this contract.
- `api/routers/session_notes.py` still targets the wrong subcollection path. Separate cleanup.
