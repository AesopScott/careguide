# Firestore Collections Registry

Every Firestore collection used in this project. For each collection: the producers (code that writes to it), consumers (code that reads from it), the rule covering it, and any composite indexes that back its queries. Mismatched producer/consumer pairs and missing rules/indexes are flagged with ⚠.

Update this file whenever a collection is added, removed, or its schema changes.

---

## `users`

Practitioner / admin / family user profiles.

**Schema (key fields):** `uid`, `email`, `full_name`, `role`, `profession`, `profession_label`, `license_states[]`, `plan`, `monthly_rate`, `beta`, `status` (`pending_activation` | `active` | `rejected`), `baa_accepted`, `created_at`, `active_at`, `rejected_at`.

**Producers**
- `api/routers/users.py:69` — register (full write)
- `api/routers/users.py:271` — set_user_status (status + timestamp)
- `admin-approvals.html:433` — updateDoc status (legacy client-side path; redundant with API)

**Consumers**
- `dashboard.html:562` — read own profile for status gate
- `admin-approvals.html:335` — list all practitioners (`where role == 'practitioner' orderBy created_at desc`)
- `family.html:524` — read practitioner profile by id
- `api/routers/users.py:241` — read in set_user_status
- `api/routers/auth_verification.py:86` — read for full_name

**Rule:** `firestore.rules` /users — self read/write + admin read/write. ✓

**Indexes:** `users` (role ASC, created_at DESC) for admin-approvals list. ✓

---

## `family_groups`

The top-level family group document. Owned by a practitioner; family members reference it via `family_group_id` claim.

**Schema (key fields):** `name`, `practitioner_id`, `care_level`, `status`, `urgent_flags[]`, `overdue_task_count`, `updated_at`, `created_at`.

**Producers**
- `new-client.html:748` — addDoc on client create
- `client.html:882, 913, 922` — updateDoc (urgent flags, etc.)

**Consumers**
- `dashboard.html:872` — list groups (`where practitioner_id == uid orderBy created_at desc`)
- `client.html:698`, `crisis-card.html:411`, `family.html:402`, `intake.html:454`, `care-plan.html:328`, `medications.html:353` — getDoc by id

**Rule:** `firestore.rules` /family_groups — owner / family-claim / admin. ✓

**Indexes:** `family_groups` (practitioner_id ASC, created_at DESC) for dashboard. ✓

---

## `parents`

Parent records, one per parent within a family group. Top-level, keyed by `family_group_id`.

**Schema (key fields):** `family_group_id`, `practitioner_id`, `first_name`, `last_name`, `care_level`, `dob`, `state`, `invite_email`, `created_at`, `updated_at`.

**Producers**
- `new-client.html:773` — addDoc on client create
- `client.html:865` — updateDoc parent details

**Consumers**
- `client.html:699`, `crisis-card.html:412`, `family.html:403` — list by `family_group_id`

**Rule:** `firestore.rules` /parents — `canAccessFamilyData` / `canWriteFamilyData`. ✓

**Indexes:** none needed (no orderBy queries).

⚠ **API mismatch:** `api/routers/parents.py:17,20,29,32` writes/reads `familyGroups/{id}/parents` (camelCase, subcollection). Collection does not exist. Dead endpoint. (Already flagged for rewrite.)

---

## `medications`

Top-level medication records keyed by `family_group_id`.

**Schema (key fields):** `family_group_id`, `name`, `dose`, `frequency`, `created_at`.

**Producers**
- `medications.html:451` — addDoc

**Consumers**
- `client.html:700`, `crisis-card.html:413`, `family.html:404` — list by `family_group_id`
- `medications.html:354` — list by `family_group_id` orderBy `created_at` desc

**Rule:** `firestore.rules` /medications — `canAccessFamilyData` / `canWriteFamilyData`. ✓

**Indexes:** `medications` (family_group_id ASC, created_at DESC). ✓

⚠ **API mismatch:** `api/routers/medications.py:19,22,37,40` writes/reads `familyGroups/{id}/medications` (camelCase, subcollection). Dead endpoint. (Already flagged.)

---

## `session_notes`

Practitioner clinical notes per family group. Top-level, keyed by `family_group_id`.

**Schema (key fields):** `family_group_id`, `practitioner_id`, `body`, `created_at`.

**Producers**
- `client.html:960` — addDoc

**Consumers**
- `client.html:701` — list by `family_group_id` orderBy `created_at` desc

⚠ **Rule:** missing. Client reads will be denied.

⚠ **Indexes:** missing. Composite needed: `session_notes` (family_group_id ASC, created_at DESC).

⚠ **API mismatch:** `api/routers/session_notes.py:17,18,31,32` writes/reads `practitioners/{uid}/sessionNotes` (subcollection under practitioners, never matches client). Dead endpoint.

---

## `care_plans`

One care plan per family group. Document id = `family_group_id`.

**Schema (key fields):** `family_group_id`, sections (goals, interventions, etc. — TBD), `created_at`, `updated_at`.

**Producers**
- `care-plan.html:447, 456` — setDoc (merge)
- `intake.html:563` — setDoc (merge from intake)

**Consumers**
- `care-plan.html:329` — getDoc by family id
- `family.html:405` — getDoc by family id

⚠ **Rule:** missing. Reads/writes will be denied.

**Indexes:** none needed (doc-id reads only).

---

## `intake_data`

Practitioner intake form data per family group. Document id = `family_group_id`.

**Schema (key fields):** `family_group_id`, intake fields (TBD), `created_at`, `updated_at`.

**Producers**
- `intake.html:575, 591` — setDoc (merge)

**Consumers**
- None currently — written but not read anywhere.

⚠ **Rule:** missing. Writes will be denied.

⚠ **Orphaned:** producer with no consumer. Either add a consumer or remove the producer.

---

## `crisis_info`

Crisis card data per family group. Document id = `family_group_id`.

**Schema (key fields):** `family_group_id`, crisis fields (contacts, escalation steps — TBD), `created_at`, `updated_at`.

**Producers**
- `crisis-card.html:500` — setDoc (merge)

**Consumers**
- `crisis-card.html:414` — getDoc by family id

⚠ **Rule:** missing.

---

## `family_messages`

Family-side messaging (family.html flow, not yet implemented end-to-end).

**Producers**
- `family.html:549` — addDoc

**Consumers**
- None currently.

⚠ **Rule:** missing. Deferred — family flow not implemented yet.

---

## `email_verification_tokens`

One-time email verification tokens. Server-only collection.

**Producers / Consumers**
- `api/routers/auth_verification.py:98, 120, 138` (set / delete / get) — Admin SDK only.

**Rule:** not needed — Admin SDK bypasses rules. ✓ (intentional)

---

## `waitlist`

Pre-launch email waitlist.

**Producers**
- (waitlist signup widget; see waitlist.html — public create)

**Consumers**
- `waitlist.html:337` — admin-only list orderBy `joinedAt` desc.

**Rule:** /waitlist — public create with field shape constraint, admin read. ✓

---

## `aiConversations`

AI chat history per user. Currently has a rule but no code path uses it.

**Rule:** ✓ (own-conversation only).

⚠ **Dead code:** no producer or consumer in the codebase. Either remove the rule or wire it up when AI chat ships.
