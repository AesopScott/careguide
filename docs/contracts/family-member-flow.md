# Feature Contract — Family Member Flow (MVP)

**Status:** locked
**Authored:** 2026-05-16
**Audit:** see [docs/contracts/family-member-flow.audit.md](family-member-flow.audit.md)

---

## In plain English

A practitioner sends an invite by email to a family member of a client they manage. The family member clicks the link, which signs them into Firebase via email-link authentication, lands them on an accept page that confirms they want to join, and drops them on a Family Dashboard showing their loved one's care plan, medications, crisis card, practitioner care updates, and a message thread with the practitioner. One family member can be invited into and access multiple family groups (multiple care receivers, possibly across multiple practitioners). Self-serve family signup is deferred to Phase 3.

## Remembers

- **Family member's user profile** (existing `users` collection): same shape as a practitioner but `role = "family"`; adds `relationship_to_parent` and a `family_group_ids` array.
- **A pending invitation record** (new `family_invitations` collection): `family_group_id`, `invited_email` (lowercased), `invited_relationship`, `expires_at`, `status` (pending / accepted / expired / revoked), `invited_by_uid`, `invited_at`, `accepted_at`. No token stored — Firebase email-link auth provides the credential. One pending invitation per (email, family_group_id) pair.
- **Care updates from practitioner to family** (new `care_updates` collection): `family_group_id`, `author_uid`, `body`, `posted_at`, optional attachment refs.
- **Family messages** (existing `family_messages` collection): two-way; family member and practitioner both write and read within the group. Rule already in place.
- **Read-only family access** to existing remembered things: `family_groups`, `parents`, `medications`, `care_plans`, `crisis_info` — gated by membership in the `family_group_ids` array claim.

## Labels

- **`family`** — set on a user when they accept their first invitation. Unlocks the family dashboard and read access to family-scoped data. Stays set even if every group is later revoked. *Setter to be built — in `/auth/accept-invite`.*
- **`family_group_ids`** — array of family_group ids the user has accepted. Mutated on each invite accept and on each revocation. *Setter to be built — same endpoint, plus the revocation endpoint.*
- **`relationship_to_parent`** — stored in the users profile, not on the token (not gating anything).

## Who can do what

| Collection / item | Practitioner (owner) | Family member (in group) | Admin |
|---|---|---|---|
| `family_invitations` | create / read / revoke for own groups | no direct access (consumed via accept endpoint) | full |
| `users` (family role) | read for any group they own | self-read, self-update | full |
| `care_updates` | create / read / update / delete | read | full |
| `family_messages` | create, read; edit/delete own | create, read; edit/delete own | full |
| `family_groups`, `parents`, `medications`, `care_plans`, `crisis_info` | full | read only, via `family_group_ids` membership | full |

## Questions between parts

- Practitioner clicks **"Invite family member"** → `POST /family-groups/{id}/invite` (body: `{ email, relationship }`) — backend creates a `family_invitations` record, calls Firebase Admin SDK to generate an email-link sign-in URL targeted at `/accept-invite.html`, sends via Brevo. *Endpoint to be built — replaces today's 501 stub.*
- Invite email link → opens `/accept-invite.html` — page detects Firebase email-link signin, prompts user to confirm their email, signs them in. *Page to be built.*
- After signin, accept page → `POST /auth/accept-invite` with the Firebase ID token — backend looks up pending invitations matching the user's email, sets `family` claim if not already set, appends the `family_group_id` to the `family_group_ids` array claim, writes/updates the users doc with `role="family"` and merges `family_group_ids`, marks the invitation accepted. *Endpoint to be built.*
- Practitioner revokes a family member → `POST /family-groups/{id}/revoke` (body: `{ uid }`) — removes that group's id from the user's `family_group_ids` claim, revokes refresh tokens so the change takes effect immediately. *Endpoint to be built.*
- Practitioner posts a care update → direct Firestore write to `care_updates` from `client.html`. No API endpoint.
- Family AI assistant → existing `POST /ai/ask`. ✓

## UI promises

- **"Invite family member"** button on `new-client.html` and `client.html` — must reach the working invite endpoint.
- **`/accept-invite.html` page** — does not exist. *To be built.*
- **Family Dashboard (`family.html`)** — exists but unreachable until claims are set. Needs an update to handle multiple `family_group_ids`: a group switcher in the header, or a "pick a family" screen if more than one is present.
- **"Care Updates" feed** on family dashboard — needs a producer UI on `client.html` and a consumer feed on `family.html`. *Both to be built.*
- **"Family settings" / "manage family members"** — out of scope, deferred to a later contract.
- **"Tasks assigned to me"** on family dashboard — out of scope, deferred (tasks collection not in this contract).
