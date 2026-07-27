---
name: git-workflow
description: Git branch naming, commit convention, and safety rules for the VDAP (VietDist Analytics Platform) capstone repo. Load before any git init/branch/commit/push in this project instead of re-deriving convention from CONTRIBUTING.md or Jira.
---

Source of truth: Jira project VDAP, Story VDAP-16 (S0.7 Branching & Commit Convention) and VDAP-11 (S0.2 Secrets Config). This file mirrors those decisions so no per-task re-lookup needed.

## Repo state
Not git-initialized yet. First git task in a session: `git init` before anything else, no untracked-work risk (nothing to lose).

## Never commit
`credentials.json`, `.env` — real Google Service Account key + secrets. Before any `git add`/`git commit`:
1. Confirm `.gitignore` has `credentials.json`, `.env`, `.venv/`, `__pycache__/`, `data/{raw,bronze,silver,gold}/*` (keep `.gitkeep`).
2. `git status` — if `credentials.json`/`.env` show as tracked/staged, stop and fix `.gitignore` first, do not commit.
3. Stage explicit paths, never `git add -A`/`git add .` blind in this repo (root has real secret file sitting next to source).

## Branch naming
`feature/VDAP-<key>-<slug>` — new work tied to a Jira issue (e.g. `feature/VDAP-31-drive-download`)
`hotfix/VDAP-<key>-<slug>` — urgent fix
No Jira key available (rare, e.g. pure chore) → `chore/<slug>`

## Commit message (Conventional Commits + Jira key)
Format: `<type>(VDAP-<key>): <imperative summary>`
Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`
Examples:
- `feat(VDAP-36): implement download_file() via Drive API`
- `fix(VDAP-58): dedup customer_master before dim build`
- `docs(VDAP-28): add Getting Started section to README`
No matching Jira key (rare) → omit scope: `chore: add .gitkeep to empty dirs`

## Defaults unless user says otherwise
- New commits, never `--amend` (see global git safety rules)
- Never push without explicit ask
- Solo project (PO = Linh Nguyen for all roles) — no PR-approval gate required, but keep Conventional Commits so history stays traceable to Jira issue keys
