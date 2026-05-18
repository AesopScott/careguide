# User Flow & UI Integration Audit — 2026-05-17

**Scope:** all personas (public, practitioner pending, practitioner active, admin, family member). All HTML pages, all API endpoints, all Firestore collections, all custom claims.

**Method:** Phase 1 = code/contract/registry cross-reference (this session). Phase 2 = live walk on `stage.parentalcareguide.com` (interactive, with the user). Phase 3 = file confirmed gaps as backlog tasks with proper dependencies.

**Motivation:** task-by-task planning has produced a backlog where prerequisite UI gaps (e.g. #17 dashboard click bug, #18 silent Brevo failure) were only discovered *after* shipping their consumers to stage. This audit catches those gaps once, against the whole project, before more tasks ship into the same trap.

---

## Personas

| ID | Persona | Auth signal | Primary surface |
|---|---|---|---|
| P0 | **Public** (unauthenticated) | none | `index.html`, marketing pages |
| P1 | **Practitioner — email unverified** | signed in, `emailVerified: false` | gated dashboard ("Check your inbox") |
| P2 | **Practitioner — pending approval** | verified, `users.status == 'pending_activation'` | gated dashboard ("waiting") |
| P3 | **Practitioner — active** | verified, `status == 'active'`, claim `practitioner: true` | `dashboard.html` + all client surfaces |
| P4 | **Practitioner — rejected** | `status == 'rejected'`, claims cleared | gated dashboard (rejected message) |
| P5 | **Admin** | claim `admin: true` (set manually via CLI script) | `admin-approvals.html` + can read/write any practitioner data |
| P6 | **Family member — accepted** | claim `family: true`, `family_group_ids: [...]` | `family.html`, accept-invite |

---

## Flow matrix

Each row is one flow the persona needs to complete. Status legend:
- ✅ Built and verified end-to-end
- 🟡 Built but unverified on live env, or partially built
- 🔴 Broken or missing in a way that blocks the persona
- ➖ Not relevant for this persona

### P0 — Public

| Flow | Entry | Status | Notes |
|---|---|---|---|
| Land on home | `index.html` | 🟡 | Page exists; verify no console errors / broken assets |
| Read "How It Works" | `how-it-works.html` | 🟡 | Page exists; verify links |
| Read BAA | `baa.html` | 🟡 | Page exists; reachable from signup checkbox |
| Submit contact form | `contact.html` → `POST /contact` | 🟡 | Endpoint verified ✓ in registry; needs live submit test |
| Join waitlist | `waitlist.html` (public create on `waitlist` collection) | 🟡 | Verify the create works and lands a doc |
| Sign up as practitioner | `signup.html` → `POST /users/register` | 🟡 | Verify register + welcome email + auto-trigger verification email |
| Sign in | `login.html` | 🟡 | Verify per-role redirect targets work |
| Read outreach materials | `outreach.html` | 🟡 | Purpose unclear from grep; verify content + audience |
| View "system map" | `build.html` | ⚠ | Reachable publicly — should this be gated? |
| View registries | `registries.html` | ⚠ | Internal/dev viewer; public exposure unintended? |
| OG card preview | `og-card.html` | ➖ | Social media meta only |

### P1 — Practitioner, email unverified

| Flow | Entry | Status | Notes |
|---|---|---|---|
| See verification gate on dashboard | `dashboard.html` → `showEmailVerifyGate()` | ✅ | Code reviewed; gate fires when `!user.emailVerified` |
| Resend verification email | dashboard gate "Resend" button → `POST /auth/send-verification` | 🟡 | Code present; verify the gate actually fires on a fresh unverified account |
| Click email link, verify | `verify-email.html` → `POST /auth/verify-email?token=...` | 🟡 | Verify the token round-trip works |

### P2 — Practitioner, pending approval

| Flow | Entry | Status | Notes |
|---|---|---|---|
| See "waiting" gate on dashboard | `dashboard.html` → `showPendingGate()` | 🟡 | Code present; verify it actually renders |
| Receive approval email | Admin clicks Approve → `POST /users/{uid}/status` → Brevo email | 🟡 | Send path exists; **prod Brevo may be broken — see #18**; once approved, practitioner must sign out + back in for token to pick up new claims |

### P3 — Practitioner, active

| Flow | Entry | Status | Notes |
|---|---|---|---|
| Sign in → dashboard | `login.html` → `dashboard.html` | 🟡 | Verify (presumably works since user has been here) |
| See own client roster | `dashboard.html` queries `family_groups where practitioner_id == uid` | ✅ | Verified live by user — shows "1 Active Client" |
| Add a client | dashboard `+ Add Client` → `new-client.html` → addDoc family_groups + parents | 🟡 | Quick-add works (user has used it); verify invite-toggle path on stage |
| **Open an existing client** | dashboard card click → `client.html?id={id}` | 🔴 | **#17 — silently bounces back to dashboard on prod.** Verified by user 2026-05-17. Blocks every downstream P3 flow. |
| Edit primary parent | `client.html` Overview → inline edit | 🟡 | Reachable only via #17; verify on stage |
| Add session note | `client.html` Session Notes tab | 🟡 | Reachable only via #17; verify on stage |
| Post care update | `client.html` Care Updates tab | 🟡 | Reachable only via #17 |
| Manage medications | `client.html` Meds tab → `medications.html` | 🟡 | Reachable only via #17 |
| View / print crisis card | `client.html` Crisis Card tab → `crisis-card.html` | 🟡 | Reachable only via #17 |
| Run AI intake | `client.html` Overview → "AI Intake →" link → `intake.html` | 🟡 | Direct-link bypass possible; `POST /ai/intake` shipped in task #1 (in-review on stage) |
| Review AI care plan | intake success → "Review Care Plan →" → `care-plan.html` | 🟡 | Reachable only via intake success path |
| Manage family members (task #2) | `client.html` Family Members tab | 🟡 | Shipped to stage; blocked from smoke test by #17 + #18 |
| Message family (task #3) | `client.html` Messages tab | 🟡 | Shipped to stage; blocked from smoke test by #17 |
| **Re-invite a family member after Add Client** | `client.html` (should have an "Invite Family" button per contract) | 🔴 | **NEW — button missing.** Contract `family-member-flow.md` UI promises both `new-client.html` and `client.html` have this; only `new-client.html` does today. The "you can resend it from the client page" warning in `new-client.html:794` is currently a lie. |
| Edit own profile (name / profession / license / beta) | (no page exists) | 🔴 | **NEW — no profile/settings page.** Practitioner can never edit after signup. |
| Delete or archive a client | (no UI) | 🔴 | **NEW — no client delete/archive.** |
| Sign out | nav → `auth.signOut()` → `login.html` | ✅ | Standard pattern present on every gated page |

### P4 — Practitioner, rejected

| Flow | Entry | Status | Notes |
|---|---|---|---|
| See rejected gate on dashboard | `dashboard.html` → `showRejectedGate()` | 🟡 | Verify content + tone |
| Get re-approved | Admin updates status `rejected → active` → token revoked, claim re-set | 🟡 | Flow exists (`api/routers/users.py` revokes refresh tokens on status change); practitioner must sign back in |

### P5 — Admin

| Flow | Entry | Status | Notes |
|---|---|---|---|
| **Sign in → land somewhere useful** | `login.html` admin branch → `/index.html` (marketing page) | 🔴 | **NEW — admin home redirects to marketing.** `login.html:270` sends admins to `/index.html`, not to an admin hub. Admin must manually type `/admin-approvals.html`. |
| Approve / reject pending practitioner | `admin-approvals.html` → `POST /users/{uid}/status` | 🟡 | Endpoint + UI exist; verify end-to-end on stage |
| View waitlist | `waitlist.html` (admin claim required) | 🟡 | Reachable directly; not linked from anywhere admin-visible |
| Manage own/any practitioner client data | client.html etc. allow admin alongside practitioner | 🟡 | Verify; needs `client.html` to work (blocked by #17) |
| **Promote a user to admin** | (no UI) | 🔴 | **NEW — admin provisioning is CLI-only** (`scripts/set-claims.mjs`). No way for an existing admin to grant admin to another user. Acceptable for a small ops team but should be a backlog item. |
| **See "all clients" / system overview** | (no UI) | 🔴 | **NEW — no admin overview.** Admin can navigate one practitioner at a time but no roll-up of the platform. (Task #10 Admin Platform Analytics partially addresses, but currently blocked by #7+#8 Supabase chain.) |

### P6 — Family member

| Flow | Entry | Status | Notes |
|---|---|---|---|
| Receive invite email | Practitioner triggers `POST /family-groups/{id}/invite` → Brevo | 🔴 | **#18 — silent Brevo failure on prod.** Verified by user 2026-05-17. Blocks every downstream P6 flow on prod. |
| Click invite link, accept | `accept-invite.html` → `POST /auth/accept-invite` → sets claims, writes user doc | 🟡 | Code reviewed; only testable once #18 clears |
| Land on family dashboard | `family.html` | 🟡 | Code reviewed; gated on `claims.family` |
| Switch between groups | `family.html` group switcher (shipped) | 🟡 | Per family-member-flow.audit |
| View parent / care plan / meds / crisis info | `family.html` reads | 🟡 | Read paths in registries; verify rendering |
| **Read messages from practitioner** | `family.html` should show a message thread | 🔴 | **NEW — family-side reader UI missing.** `family.html` can SEND messages (`addDoc family_messages` line 646) but has no UI to READ them. Contract promises two-way thread. |
| Send message to practitioner | `family.html` Send Message button | 🟡 | Producer wired; consumer (practitioner) shipped via task #3 (in-review) |
| **Ask AI** | `family.html` should call `POST /ai/ask` per contract | 🔴 | **NEW — Family AI assistant not wired.** Endpoint exists (`api/routers/ai.py`) as orphan; family.html has no UI for it. |
| Sign out | nav → `auth.signOut()` | 🟡 | Verify reachable |

---

## Cross-cutting findings

### Bug class — silent redirects

`#17` (dashboard → client) silently redirects back. The same pattern (`if (!snap.exists()) window.location.href = '/dashboard.html'`) exists in **every page that takes an `?id=` param**: `client.html:734`, `intake.html:439` (different — redirects when no id at all), `care-plan.html`, `medications.html`, `crisis-card.html`. Whatever root-cause #17 turns out to be (Firestore rule difference, auth race, or id mismatch), the defensive fix should be applied to all of these.

→ Becomes part of task #17's plan.

### Bug class — silent server-side failures with HTTP 200

`#18` (Brevo failure not surfaced) is one instance of a broader pattern: endpoints that catch a downstream service failure, log it, and return 200 with `{success: true, warning: "..."}`. The client only checks `!res.ok`. Affected: `POST /family-groups/{id}/invite` (Brevo), `POST /ai/intake` (if Claude parse fails — task #1 addresses), possibly `POST /users/register` (welcome email is best-effort).

→ Either change endpoints to fail-fast (return 5xx when the downstream actually broke), OR change every consumer to inspect the response body for warnings. Both options viable; pick one and apply across the codebase.

### Orphan endpoints (cleanup candidates)

- `POST /ai/care-plan-draft` — no caller
- `POST /ai/session-note-draft` — no caller
- `POST /notifications/email`, `/sms`, `/reminder` — no caller (intended internal but never called)
- `GET/POST /family-groups/`, `GET /family-groups/{id}` — no caller (client uses direct Firestore)
- All `/parents/`, `/medications/`, `/session-notes/` CRUD — clients use direct Firestore; tracked by task #6 (in queue)

→ Existing task #6 covers `/parents`, `/medications`, `/session-notes`. The ai/care-plan-draft, ai/session-note-draft, notifications/*, and family-groups GET endpoints should be folded into #6 or filed as a separate cleanup.

### Dead code

- `aiConversations` Firestore rule exists but no producer or consumer in the code.

→ Either remove the rule or wire it up. Probably remove.

### Operational dependencies (not code)

- **Firebase Email-Link sign-in** must be enabled in Firebase Console (Auth → Sign-in method → Email/Password → Email link). The family-member-flow.audit.md flagged this. If it's disabled, `POST /family-groups/{id}/invite` returns an actionable error. Worth verifying on both stage and prod.
- **Brevo credentials** must be present in the Cloud Run env for each environment. Possibly the root cause of #18 on prod. Verify on prod, stage, and (if separate) any preview environments.

### Dev / internal pages exposed publicly

- `build.html` — "System Map"
- `registries.html` — registries viewer

If these were intended internal, they need an auth gate (admin claim at minimum). If they're intentionally public for transparency, document that decision.

### Token-refresh assumption

The current model assumes that when a user's claims change (admin approves, rejects, revokes a family group), the user signs out and back in to pick up the new claims. There's no in-app prompt or refresh mechanism. Worth documenting in the family-member-flow contract and verifying that the rejection/re-approval flow doesn't silently leave a user with a stale token.

---

## Proposed new backlog tasks

Numbered #19 onward to avoid collision with PR #16's #17/#18 and the in-flight backlog PRs #7/#8/#9 still claiming #11–14.

| # | Title | Category | Status | Depends on | Notes |
|---:|---|---|---|---|---|
| 19 | "Invite family member" button on `client.html` (re-invite / late-invite path) | debt | backlog | — | Contract gap; the warning in `new-client.html:794` already promises this exists |
| 20 | Family-side message thread reader UI on `family.html` | debt | backlog | 18 | Two-way thread promised; producer wired, consumer missing on family side |
| 21 | Wire `POST /ai/ask` into a family AI assistant on `family.html` | feature | backlog | — | Endpoint exists as orphan; UI never built |
| 22 | Admin home / hub page | feature | backlog | — | Login currently sends admins to `/index.html`; needs a dedicated admin landing with links to admin-approvals, waitlist, future overview |
| 23 | Practitioner profile / settings page | feature | backlog | — | Edit name / profession / license states / beta after signup; possibly delete account |
| 24 | Client delete / archive flow | feature | backlog | — | No way to remove or archive a `family_group` once created |
| 25 | Defensive error UI on every `?id=`-driven page (apply #17's fix broadly) | debt | backlog | 17 | Once #17 root cause is fixed, apply the same defensive pattern to `intake.html`, `care-plan.html`, `medications.html`, `crisis-card.html` |
| 26 | Audit & convert silent-warning 200s to fail-fast 5xx (apply #18's fix broadly) | debt | backlog | 18 | Same root pattern in `/ai/intake` parse-fail and possibly `/users/register` welcome email |
| 27 | Cleanup additional orphan endpoints (ai/care-plan-draft, ai/session-note-draft, notifications/*, family-groups GETs) | debt | backlog | — | Extends #6 scope; either remove or wire callers |
| 28 | Remove `aiConversations` rule (or wire the AI conversations UI) | debt | backlog | — | Dead rule |
| 29 | Gate or remove `build.html` and `registries.html` for non-admin users | debt | backlog | — | Currently public; decide intent |
| 30 | Admin-grants-admin UI (replace CLI `set-claims.mjs` provisioning) | feature | backlog | 22 | Acceptable to defer until admin team grows; depends on admin hub existing |
| 31 | Verify Firebase Email-Link sign-in is enabled on stage and prod | ops | backlog | — | Manual ops check; if a different Firebase account, document |

~~| 32 | Verify Brevo credentials present on stage Cloud Run | ops | backlog | 18 |~~ — **dropped after Phase 2 walk**; Brevo broken on both envs, folded into #18.

Categories beyond the existing set (`debt`, `infrastructure`, `feature`, `emergency-fix`) introduce one new: **`ops`** (user-confirmed Phase 2) for operational/console tasks that don't touch code.

---

## Phase 2 — live walk results (2026-05-17, same session)

Important environment fact discovered during the walk: **stage and prod share the same Firebase project (`careguide-def76`)** — same Auth, same Firestore. Only the FastAPI Cloud Run service (`careguide-api` vs `careguide-api-stage`) and the static frontend deploy are duplicated. Implications:
- Practitioner accounts work identically on both envs.
- The "1 active client" visible on the stage dashboard IS the same `family_groups` doc as on prod.
- Bugs that depend on Firestore data, Firestore rules, or shared frontend code reproduce on both envs.
- Bugs that depend on Cloud Run env vars (Brevo creds, etc.) can differ per service.

### Flow 1 — practitioner opens existing client (stage)

**Result:** clicking the client card on stage bounces back to dashboard, identical to prod. Same data, same `client.html` code, same Firestore rules → **#17 confirmed code-level, environment-agnostic**. Fix will ship to both envs via the next stage→main rollup. Updated #17 description below to reflect this.

### Flow 2 — family member loop (stage)

**Sub-step 2a result:** triggered an invite from new-client.html on stage with a fresh test email. **Nothing arrived in Brevo's outbound log.** So Brevo is broken on **both** the stage AND prod Cloud Run services — not prod-only. #18 scope expanded accordingly; the proposed standalone task #32 ("verify Brevo on stage") is dropped — folded into #18 because both services need the same fix.

**Sub-steps 2b–2e (accept flow, family.html UX walk):** not executable until #18 clears. Deferred. Once Brevo works on stage we can resume against a fresh test invite to verify tasks #20, #21, and confirm task #2's revoke flow end-to-end.

### Flow 3 — admin sign-in landing

Confirmed from code, no live walk needed (the active practitioner account is not an admin; user's separate admin account works on both envs but the code at `login.html:270` is unambiguous: admin → `/index.html`). **Task #22 (admin home page) confirmed real.**

### Flow 4 — public surface

**4a result:** both `build.html` and `registries.html` load fully unauthenticated on stage. **Task #29 (gate or remove dev pages) confirmed real.**

**4b result:** quick spot-check of marketing pages — no obvious breakage. No new tasks.

### Net result of Phase 2

- **#17, #18, #22, #29 all confirmed real.** No false positives.
- **#32 dropped** (folded into #18 — both envs broken, same Brevo fix).
- **Phase 2 family-member walks deferred** until #18 clears Brevo.

---

## Methodology notes (for future `/flow-audit` skill extraction)

What worked:
1. Building the persona table first, before touching code, kept the analysis grounded in "who needs what."
2. Cross-referencing the family-member-flow contract against the as-built code immediately surfaced "promised but missing" gaps (the `client.html` invite button, the family AI assistant) — gaps that a code-only audit would miss because there's nothing wrong with the code that exists.
3. The flow matrix (persona × flow → status) made it easy to see whole-persona blockers (e.g., P6 is entirely blocked until #18 clears) versus individual feature gaps.

What to formalize in a future skill:
- Step 1: enumerate personas from auth code (`claims.*` checks) and contracts.
- Step 2: enumerate every HTML page and tag its persona + auth gate.
- Step 3: for each persona, enumerate intended flows from contracts (or interview the user if no contract exists).
- Step 4: build the matrix; populate from code where possible.
- Step 5: interactive walk with the user to flip 🟡 → ✅ or 🔴.
- Step 6: file gaps as backlog tasks with proper deps; reorder priorities.
- Step 7: write audit report to `docs/audits/{date}-flow-audit.md`; PR includes both.

The whole pass takes one focused session and produces both immediate backlog hygiene and ongoing documentation a future audit can diff against.
