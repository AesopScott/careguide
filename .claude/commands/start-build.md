# /start-build [task-number]

You are beginning a focused build session for the CareGuide project.

## Task Selection

If a task number was provided as an argument (`$ARGUMENTS`), fetch that specific task.
If no argument was provided, automatically select the next available task.

### How to fetch tasks

Call the CareGuide API to read from the task board:

**Auto-select (no arg):**
```
GET https://careguide-api-658340465706.us-central1.run.app/tasks?status=ready&limit=1&sort=priority
```
Pick the first result (highest priority, oldest created_at as tiebreaker).

**Specific task:**
```
GET https://careguide-api-658340465706.us-central1.run.app/tasks/{task-number}
```

If the API is not yet available (task board not built), read from `/docs/backlog.json` instead and select accordingly.

### Mark the task in-progress

```
PATCH https://careguide-api-658340465706.us-central1.run.app/tasks/{task-number}
Body: { "status": "in-progress", "branch": "<branch-name>" }
```

## Branch and Worktree Setup

Create a branch name from the task: `task/{number}-{slug}` where slug is the title lowercased, spaces replaced with hyphens, max 40 chars.

Create an isolated git worktree:
```bash
git worktree add ../careguide-task-{number} -b task/{number}-{slug}
```

Tell the user the worktree path and branch name.

## Load Context

Before starting, read these files in full:
- The task's `description` and `plan` fields (from the API response)
- `/docs/registries/collections.md`
- `/docs/registries/endpoints.md`
- `/docs/registries/claims.md`

If the task has dependencies, check that those tasks have status `done` before proceeding. If they don't, stop and inform the user.

## Begin

Summarize:
1. Task number, title, and description
2. Branch and worktree created
3. Any dependencies and their status
4. Your intended first step

Then ask the user to confirm before writing any code.
