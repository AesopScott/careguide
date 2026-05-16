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
- ⚠ **None.** Not set anywhere in the codebase.

**Checkers**
- `login.html:273` — redirect to `/family.html`
- `crisis-card.html:396`, `medications.html:337` — allowed alongside practitioner/admin
- `family.html:368` — required (else show waiting state)

⚠ **CRITICAL:** consumer-only. Family-member flow is non-functional until a setter is built.

---

## `family_group_id`

The family group a family-member user belongs to.

**Setters**
- ⚠ **None.** Not set anywhere in the codebase.

**Checkers**
- `family.html:375` — read into local `familyId`
- `firestore.rules` /family_groups read — `request.auth.token.family_group_id == groupId`
- `firestore.rules` /parents, /medications read — via `canAccessFamilyData(familyGroupId)`

⚠ **CRITICAL:** consumer-only. Required for the entire family-member data path. Until set, family members can read nothing.

---

## Summary

| Claim             | Producers | Consumers | Status                |
|-------------------|-----------|-----------|-----------------------|
| admin             | manual    | many      | ✓                     |
| practitioner      | API       | many      | ✓ (UX gap on re-approve) |
| profession        | API       | none      | ⚠ orphan              |
| beta              | API       | none      | ⚠ orphan (planned)    |
| family            | none      | many      | ⚠ missing setter      |
| family_group_id   | none      | many + rules | ⚠ missing setter   |
