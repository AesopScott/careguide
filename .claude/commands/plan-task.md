# /plan-task [task-number]

You are a planning agent for the CareGuide project. Your job is to take a task from the backlog and produce a concrete implementation plan before any build session touches it.

## Step 1 — Load the task

```
GET https://careguide-api-658340465706.us-central1.run.app/tasks/{task-number}
```

If the API is unavailable, read from `/docs/backlog.json` and find the task by number.

If the task already has a `plan` field with content, ask the user whether to revise it or start fresh.

## Step 2 — Load boundary contracts

Read in full:
- `/docs/registries/collections.md`
- `/docs/registries/endpoints.md`
- `/docs/registries/claims.md`
- `/docs/contracts/` — any relevant feature contracts

Also read any source files directly relevant to the task (the task description should hint at which ones).

## Step 3 — Identify all boundary changes

Before planning implementation steps, enumerate every cross-boundary change this task requires:

- **New Firestore collections** — name, producers, consumers, rules needed, indexes needed
- **Modified collections** — new fields, new access patterns, rule changes
- **New API endpoints** — path, method, auth middleware, request/response shape, callers
- **Modified endpoints** — shape changes, new auth requirements
- **New custom claims** — name, who sets it, who checks it
- **New frontend pages or significant UI sections** — auth guard needed?

Flag any conflict with existing boundaries (e.g., a new collection name that already exists, a claim that's already set differently).

## Step 4 — Produce the implementation plan

Write a step-by-step plan in this order (skip steps that don't apply):

1. Registry updates — update docs first, before any code
2. Firestore rules changes
3. Firestore index additions (`firestore.indexes.json`)
4. Backend: new/modified routers, services, models
5. Frontend: new/modified HTML pages, JS logic
6. Wiring: ensure all producers and consumers are connected
7. Verification: how to manually confirm the feature works end-to-end

Each step should be specific enough that a build session can execute it without ambiguity.

## Step 5 — Check dependencies

List any other tasks this plan depends on. If a dependency is not `done`, flag it clearly.

## Step 6 — Save the plan

If the API is available:
```
PATCH https://careguide-api-658340465706.us-central1.run.app/tasks/{task-number}
Body: { "plan": "{the plan text}", "status": "ready" }
```

If not available, output the plan and tell the user to save it manually.

## Step 7 — Report

Output the full plan to the user and confirm it was saved. Ask if they want to adjust anything before a build session picks it up.
