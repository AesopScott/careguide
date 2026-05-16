# Firebase Custom Claims Registry

Every custom claim used to gate access in this project. For each claim: where it gets set on a user, every place it's checked, and any mismatch.

Update this file whenever a claim is added, removed, or a new check is added.

---

## `admin`

Marks a user as a platform administrator. Granted manually — there is no UI for it.

**Setters**
- `scripts/set-claims.mjs` — manual CLI: `node scripts/set-claims.mjs <uid> '{"admin":true}'`
- `scripts/set-admin.js` — alternate manual script.

**Checkers (client)**
- `login.html:268` — redirect to `/index.html` (admin home)
- `dashboard.html:549, 554` — gate access; admins skip status check
- `admin-approvals.html:309` — required to view page
- `care-plan.html:312, 447` — allowed alongside practitioner
- `intake.html:447` — allowed alongside practitioner
- `crisis-card.html:396` — allowed alongside practitioner and family
- `medications.html:337` — allowed alongside practitioner and family
- `new-client.html:651` — allowed alongside practitioner
- `client.html:681` — allowed alongside practitioner
- `family.html:365` — redirect away to dashboard if admin

**Checkers (rules)**
- `firestore.rules` /users — admin read/write on any user doc
- `firestore.rules` /family_groups — admin read/update/delete
- `firestore.rules` /parents, /medications — admin via `canAccessFamilyData` / `canWriteFamilyData`
- `firestore.rules` /waitlist — admin read/update/delete

**Status:** ✓ wired correctly. Manual provisioning is the documented path.

---

## `practitioner`

Marks an approved practitioner.

**Setters**
- `api/routers/users.py:58` — set on `/users/register` (immediately at signup; status is `pending_activation`)
- `api/routers/users.py:254` — re-set on approve `/users/{uid}/status` with `status='active'`
- `api/routers/users.py:260` — **cleared** (set to `{}`) on reject

**Checkers (client)**
- `login.html:271` — redirect to `/dashboard.html`
- `dashboard.html:549` — required to view page
- `care-plan.html:312`, `intake.html:447`, `crisis-card.html:396`, `medications.html:337`, `new-client.html:651`, `client.html:681` — required (with admin / family alternatives where applicable)
- `family.html:365` — redirect away to dashboard if practitioner

**Checkers (rules)**
- `firestore.rules` `isPractitioner()` — used by /family_groups create rule.

**Edge case (handled):** rejected → re-approved practitioners would otherwise have stale tokens. `api/routers/users.py` now calls `firebase_auth.revoke_refresh_tokens(uid)` on rejection and on re-approval from rejected, forcing the next request to fail and the user to re-authenticate. ✓

---

## `profession`

The practitioner's discipline (`gcm`, `elder_law`, `social_work`, `financial`).

**Setters**
- `api/routers/users.py:60, 256` — set alongside `practitioner` claim.

**Checkers**
- None — never read from the token. Practitioner UI reads from the Firestore user profile instead.

⚠ **Orphaned:** producer with no consumer. Either remove the claim or use it for client-side gating (would avoid an extra Firestore read).

---

## `beta`

Beta-tester flag.

**Setters**
- `api/routers/users.py:61, 257` — defaults to `True`.

**Checkers**
- None currently.

⚠ **Orphaned:** producer with no consumer. Intended for future billing gating; safe to leave but document the plan.

---

## `family`

Marks an approved family member with access to `family.html`.

**Setters**
- `api/routers/auth_verification.py` accept_invite — sets on first invite acceptance; remains set even if all groups are later revoked.

**Checkers**
- `login.html:273` — redirect to `/family.html`
- `crisis-card.html:396`, `medications.html:337`, `care-plan.html:312` — allowed alongside practitioner/admin
- `family.html:368` — required (else show waiting state)

**Status:** ✓ wired.

---

## `family_group_ids`

Array of family group ids the family-member user has accepted invitations into. Replaces the planned-but-never-used singular `family_group_id`.

**Setters**
- `api/routers/auth_verification.py` accept_invite — appends new group id (dedup).
- `api/routers/family_groups.py` revoke_family_member — removes a group id; revokes refresh tokens for immediate effect.

**Checkers**
- `family.html` — reads into local state, populates group switcher (falls back to legacy singular for any pre-migration accounts).
- `firestore.rules` `inFamilyGroups(groupId)` helper — used by /family_groups read, `canAccessFamilyData` (parents, medications, care_plans, crisis_info reads), family_messages read.

**Status:** ✓ wired. The legacy singular `family_group_id` claim has been retired from rules but `family.html` keeps a fallback read of it for any user accounts provisioned before the array was introduced.

---

## Summary

| Claim             | Producers | Consumers | Status                |
|-------------------|-----------|-----------|-----------------------|
| admin             | manual    | many      | ✓                     |
| practitioner      | API       | many      | ✓                     |
| profession        | API       | none      | ⚠ orphan              |
| beta              | API       | none      | ⚠ orphan (planned)    |
| family            | API       | many      | ✓                     |
| family_group_ids  | API       | many + rules | ✓                  |
