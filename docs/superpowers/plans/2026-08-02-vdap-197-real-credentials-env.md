# VDAP-197 Real credentials.json + .env Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the real local `.env` so `gdrive_connector.py` can resolve `GOOGLE_SERVICE_ACCOUNT_JSON` to the already-present real `credentials.json`, and prove neither file can ever leak into a commit.

**Architecture:** Local-machine-only file. No application code changes. `credentials.json` already exists at repo root (real Service Account key, present since 2026-07-29). This ticket only adds `.env` and verifies both stay outside git's tracked set.

**Tech Stack:** dotenv convention, `python-dotenv` (`load_dotenv()` already called in `gdrive_connector.py`).

## Global Constraints

- **CRITICAL — this is the whole point of the ticket:** the `.env` created here must NEVER be `git add`ed or committed. There is no commit step in this plan for `.env` or `credentials.json` — only verification that git refuses to track them.
- AC (VDAP-197): `git add .` does not stage `credentials.json`/`.env`; `os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")` returns the correct path.
- Confirmed pre-conditions: `credentials.json` exists (2344 bytes), `.gitignore` already matches both `credentials.json` and `.env` (verified in VDAP-189/earlier).

---

### Task 1: Create real .env, verify it and credentials.json can't be committed

**Files:**
- Create: `.env` (repo root, NOT committed — local only)

**Interfaces:**
- Consumes: `credentials.json` (already on disk)
- Produces: `GOOGLE_SERVICE_ACCOUNT_JSON` env var that `gdrive_connector.py:15`'s `os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials.json")` reads — VDAP-36 (`download_file()` implementation, Epic 1) depends on this resolving correctly.

- [ ] **Step 1: Create `.env` with the real path**

File content:
```
GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json
```

- [ ] **Step 2: Verify `git add .` does not stage either secret file (AC)**

Run:
```bash
git add .
git status --short
git reset
```
Expected: `git status --short` output contains no line for `credentials.json` or `.env` (they must not appear as `A ` staged entries — `git add .` silently skips gitignored files). `git reset` undoes any accidental staging of unrelated files before the next step.

- [ ] **Step 3: Verify `os.getenv` resolves the real credentials path (AC)**

Run:
```bash
uv run python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))"
```
Expected output: `credentials.json`

- [ ] **Step 4: Verify gdrive_connector.py's own resolution matches (exercises the real code path, not just os.getenv directly)**

Run:
```bash
uv run python -c "import gdrive_connector; print(gdrive_connector.SERVICE_ACCOUNT_FILE)"
```
Expected output: `credentials.json` (confirms `gdrive_connector.py` picks up the `.env` value, not just its hardcoded default — both happen to be `"credentials.json"` here, but this proves the `.env` is actually being read, not silently ignored).

- [ ] **Step 5: No commit — confirm working tree has nothing new to commit for this ticket**

Run: `git status --short`
Expected: no `credentials.json`/`.env` lines. Only the plan doc itself (`docs/superpowers/plans/2026-08-02-vdap-197-real-credentials-env.md`) is a trackable new file — commit that alone, nothing else.

```bash
git add docs/superpowers/plans/2026-08-02-vdap-197-real-credentials-env.md
git commit -m "docs(VDAP-197): record real credentials.json + .env setup verification"
```

---

## Self-Review

**1. Spec coverage:** Technical Steps (copy `credentials.json` — already present; create `.env`; `git check-ignore -v`; `git status`) → Steps 1-2, 5. AC (`git add .` doesn't stage; `os.getenv` resolves) → Steps 2-4. Covered, no gaps.
**2. Placeholder scan:** No TBD/TODO — every step is a real command against the real (already-present) credentials file.
**3. Type consistency:** N/A (no code changes — only reads existing `gdrive_connector.py:15`'s `SERVICE_ACCOUNT_FILE` constant).
