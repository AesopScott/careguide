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

**API:** `api/routers/parents.py` writes/reads top-level `parents` filtered by `family_group_id`. CRUD endpoints (create, list, get/patch/delete by id) all enforce ownership of the parent's `family_group`. ✓

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

**API:** `api/routers/medications.py` writes/reads top-level `medications` filtered by `family_group_id` (uses created_at index for list). CRUD endpoints (create, list, get/patch/delete by id) all enforce ownership of the med's `family_group`. ✓

---

## `session_notes`

Practitioner clinical notes per family group. Top-level, keyed by `family_group_id`.

**Schema (key fields):** `family_group_id`, `practitioner_id`, `body`, `created_at`.

**Producers**
- `client.html:960` — addDoc

**Consumers**
- `client.html:701` — list by `family_group_id` orderBy `created_at` desc

**Rule:** `firestore.rules` /session_notes — practitioner who owns the group + admin. No family read. ✓

**Indexes:** `session_notes` (family_group_id ASC, created_at DESC). ✓

⚠ **API mismatch:** `api/routers/session_notes.py:17,18,31,32` writes/reads `practitioners/{uid}/sessionNotes` (subcollection, never matches client). Dead endpoint — flagged for rewrite.

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

**Rule:** `firestore.rules` /care_plans — practitioner full access, family read, admin full access. ✓

**Indexes:** none needed (doc-id reads only).

---

## `intake_data`

Practitioner intake form data per family group. Document id = `family_group_id`.

**Schema (key fields):** `family_group_id`, intake fields (TBD), `created_at`, `updated_at`.

**Producers**
- `intake.html:575, 591` — setDoc (merge)

**Consumers**
- None currently — written but not read anywhere.

**Rule:** `firestore.rules` /intake_data — practitioner-only (no family access). ✓

⚠ **Orphaned:** producer with no consumer. Either add a consumer or remove the producer.

---

## `crisis_info`

Crisis card data per family group. Document id = `family_group_id`.

**Schema (key fields):** `family_group_id`, crisis fields (contacts, escalation steps — TBD), `created_at`, `updated_at`.

**Producers**
- `crisis-card.html:500` — setDoc (merge)

**Consumers**
- `crisis-card.html:414` — getDoc by family id

**Rule:** `firestore.rules` /crisis_info — practitioner full access, family read (emergency access), admin full access. ✓

---

## `family_messages`

Family-side messaging (family.html flow, not yet implemented end-to-end).

**Producers**
- `family.html:549` — addDoc

**Consumers**
- None currently — practitioner-side reader not yet built.

**Rule:** `firestore.rules` /family_messages — both practitioner and family member can read/write within their group; only the sender (or admin) can edit/delete. ✓

⚠ **Note:** rule is in place but the family flow itself (claim setters, accept-invite, message UI on practitioner side) is not implemented. Writes from family.html will succeed once the claim is set.

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
