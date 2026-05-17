# /finish-build

You are completing a build session for the CareGuide project. Your job is to verify the work, commit it cleanly, push, open a PR, and update the task board.

## Step 1 — Identify the current task

Read the current branch name to extract the task number:
```bash
git branch --show-current
```
The branch name format is `task/{number}-{slug}`. Extract `{number}`.

Fetch the task spec:
```
GET https://careguide-api-658340465706.us-central1.run.app/tasks/{number}
```

## Step 2 — Verify against the task spec

Before committing, check:
- Does the implementation match the task `description` and `plan`?
- Are all Firestore collections, endpoints, or claims introduced in this task reflected in the registries (`/docs/registries/`)? If not, update the registries now.
- Are there any files changed that fall outside the scope of this task? Flag them to the user before proceeding.

If anything is out of scope or missing, stop and resolve with the user.

## Step 3 — Commit

Stage and commit only files relevant to this task. Write a clear commit message:
```
git commit -m "$(cat <<'EOF'
{type}: {short description}

Task #{number} — {task title}

{1-2 sentences on what was built and why}
EOF
)"
```

## Step 4 — Push

```bash
git push -u origin task/{number}-{slug}
```

Retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s) on network failure.

## Step 5 — Open a PR

Use the GitHub MCP tools to create a pull request:
- **Base branch:** `main`
- **Title:** `Task #{number}: {task title}`
- **Body:** Include the task description, what was built, what registries were updated, and the test plan. End with the task number for traceability.

Do NOT merge the PR. Leave it open for review.

## Step 6 — Update the task board

```
PATCH https://careguide-api-658340465706.us-central1.run.app/tasks/{number}
Body: { "status": "in-review", "pr_url": "{pr url}" }
```

## Step 7 — Report to the user

Summarize:
- What was committed
- PR URL
- Task marked as in-review
- Any registry files updated
- Suggested next: run `/review-pr {pr-number}` in a review session
