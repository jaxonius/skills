---
name: kanboard
description: Interact with a self-hosted Kanboard instance over its JSON-RPC API — list/create projects, manage tasks (create, move between columns, comment, open/close), and query boards. Use when the user wants to read or update a Kanboard board, sync work items to Kanboard, or automate task management against a Kanboard server.
---

# Kanboard

[Kanboard](https://github.com/kanboard/kanboard) is self-hosted Kanban project-management
software. It exposes everything through a **JSON-RPC 2.0 API** at `/jsonrpc.php`, which this
skill drives.

## When to use this skill

- The user references a Kanboard instance, board, or task and wants to read or change it.
- The user wants to push/sync work items, tickets, or TODOs into Kanboard.
- Any automation against a Kanboard server (reporting, bulk task creation, moving cards).

## Setup — credentials

The API needs three things. Read them from the environment; **never** hardcode a token in a
file or commit it.

| Variable | Meaning |
| --- | --- |
| `KANBOARD_URL` | Base URL of the instance, e.g. `https://kanboard.example.com` (the helper appends `/jsonrpc.php`). |
| `KANBOARD_USER` | `jsonrpc` for the **Application API** (no permission checks), or a real username for the **User API**. |
| `KANBOARD_TOKEN` | The API token (Settings → API for the app token) or the user's password / personal access token. |

> Users with two-factor auth enabled must use a **personal access token**, not their password.

If any are missing, ask the user for them (or where to find them) before calling the API.

## How to call the API

Use the bundled helper — it handles JSON-RPC envelope, auth, and error reporting:

```bash
python scripts/kanboard.py <method> '<json-params>'
```

Examples:

```bash
# Sanity check / get the logged-in app version
python scripts/kanboard.py getVersion

# List all projects
python scripts/kanboard.py getAllProjects

# Get one project by id
python scripts/kanboard.py getProjectById '{"project_id": 1}'

# Create a task
python scripts/kanboard.py createTask '{"title": "Fix login bug", "project_id": 1, "column_id": 2}'

# Move a task to another column
python scripts/kanboard.py moveTaskPosition '{"project_id": 1, "task_id": 42, "column_id": 3, "position": 1, "swimlane_id": 1}'

# Close a task
python scripts/kanboard.py closeTask '{"task_id": 42}'
```

The helper prints the `result` field on success and exits non-zero with the JSON-RPC `error`
on failure.

### Raw curl (if Python is unavailable)

```bash
curl -sS -u "$KANBOARD_USER:$KANBOARD_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"getAllProjects","id":1}' \
  "$KANBOARD_URL/jsonrpc.php"
```

## Common workflows

**Find the right column before creating/moving a task.** Column ids are per-project and not
guessable. Call `getColumns` with `{"project_id": N}` to map column names → ids, then use the id.

**Create a task on a board:**
1. `getAllProjects` → find the `project_id`.
2. `getColumns {"project_id": N}` → find the target `column_id`.
3. `createTask {"title": "...", "project_id": N, "column_id": C, "description": "...", "owner_id": U}`.

**Report board state:** `getBoard {"project_id": N}` returns the full swimlane/column/task
structure in one call — prefer it over many `getAllTasks` calls.

## Procedure reference (most-used)

Full list: <https://docs.kanboard.org/v1/api/>

### Projects
- `getAllProjects` — all projects.
- `getProjectById {project_id}` / `getProjectByName {name}`.
- `createProject {name, description?, owner_id?}`.

### Board / columns
- `getBoard {project_id}` — full board (swimlanes → columns → tasks).
- `getColumns {project_id}` — columns with ids.

### Tasks
- `createTask {title, project_id, color_id?, column_id?, owner_id?, date_due?, description?, category_id?, score?, swimlane_id?, priority?, tags?}` — returns new task id.
- `getTask {task_id}` — one task.
- `getAllTasks {project_id, status_id}` — `status_id` 1 = active, 0 = inactive.
- `updateTask {id, title?, owner_id?, date_due?, description?, ...}`.
- `moveTaskPosition {project_id, task_id, column_id, position, swimlane_id}`.
- `openTask {task_id}` / `closeTask {task_id}` — reopen / close.
- `removeTask {task_id}` — delete.

### Comments
- `createComment {task_id, user_id, content}`.
- `getAllComments {task_id}`.

### Users
- `getMe` — current user (User API only).
- `getUser {user_id}` / `getAllUsers`.

## Notes & gotchas

- The Application API (`jsonrpc` user) **cannot** call `getMe` or any `My…` procedures and
  bypasses permission checks — use a real user for permission-sensitive work.
- All requests must be `POST`. The helper enforces this.
- Ids (`column_id`, `swimlane_id`, `owner_id`, `category_id`) are instance-specific — always
  look them up rather than assuming.
- Booleans returned `true`/`false` mean success/failure for mutating calls.
