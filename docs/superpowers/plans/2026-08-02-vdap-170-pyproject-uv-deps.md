# VDAP-170 Init pyproject.toml + uv deps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize `uv`-managed Python project (`pyproject.toml` + `uv.lock`) with the core dependencies the Bronze ingestion pipeline needs.

**Architecture:** Single `uv init` call scaffolds `pyproject.toml`; a single `uv add` call resolves and locks all 7 core dependencies in one pass. No application code changes.

**Tech Stack:** uv 0.11.14, Python 3.11+.

## Global Constraints

- Package list (exact, from Jira VDAP-170 Technical Notes): `polars google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv fastexcel pytest`
- AC: `uv run python -c "import polars, googleapiclient"` must exit 0.
- No `credentials.json`/`.env`/`jira.env` touched (out of scope, already gitignored).

---

### Task 1: Init uv project + add core deps

**Files:**
- Create: `pyproject.toml`
- Create: `uv.lock`

**Interfaces:**
- Consumes: nothing (first task in ticket)
- Produces: `pyproject.toml` with `[project.dependencies]` containing the 7 packages above; later tickets (VDAP-171+) assume `uv run`/`uv sync` works from repo root.

- [ ] **Step 1: Run `uv init` in repo root (non-interactive, no app template)**

Run: `cd /Users/anhtran/Desktop/vietdist-analytics-platform && uv init --no-readme --no-workspace .`
Expected: creates `pyproject.toml` (and `main.py` stub — delete it, repo already has `gdrive_connector.py` as entry point, no need for uv's placeholder).

- [ ] **Step 2: Add the 7 core dependencies**

Run: `uv add polars google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv fastexcel pytest`
Expected: `uv.lock` created/updated, `pyproject.toml` `dependencies` array lists all 7 packages, exit code 0.

- [ ] **Step 3: Remove uv's placeholder `main.py` if created**

Run: `rm -f main.py` (only if Step 1 created it — repo uses `gdrive_connector.py`, not a generated stub)

- [ ] **Step 4: Verify the AC import command**

Run: `uv run python -c "import polars, googleapiclient"`
Expected: no output, exit code 0 (no ImportError).

- [ ] **Step 5: Verify `uv sync` is clean on a fresh resolve**

Run: `uv sync`
Expected: "Resolved N packages" / "Audited N packages" — no errors.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat(VDAP-170): init pyproject.toml + uv add core deps"
```

---

## Self-Review

**1. Spec coverage:** Technical Notes = 1 `uv init` + 1 `uv add` command → Task 1 covers both. AC = 1 import check → Step 4. Both covered, no gaps.
**2. Placeholder scan:** No TBD/TODO — every step is a real command.
**3. Type consistency:** N/A (no functions/interfaces introduced beyond a config file).
