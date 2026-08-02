# VDAP-193 .env.example Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Commit a `.env.example` so anyone cloning the repo knows exactly which env var to set, without ever seeing a real secret value.

**Architecture:** Single dotenv-format file at repo root, one variable, placeholder value = the filename convention (`credentials.json`), not a real key.

**Tech Stack:** dotenv convention (consumed by `python-dotenv`'s `load_dotenv()` in `gdrive_connector.py`).

## Global Constraints

- Confirmed env var name (`gdrive_connector.py:15`): `GOOGLE_SERVICE_ACCOUNT_JSON`, default `"credentials.json"` if unset.
- AC: `.env.example` committed to git, contains no real key/token — only the placeholder filename.
- `.gitignore` already excludes `.env` (real file) but NOT `.env.example` — must stay that way so this file gets committed.

---

### Task 1: Create and commit .env.example

**Files:**
- Create: `.env.example`

**Interfaces:**
- Consumes: nothing
- Produces: documents the `GOOGLE_SERVICE_ACCOUNT_JSON` var that VDAP-197 (place real `.env`) and `gdrive_connector.py` both rely on.

- [ ] **Step 1: Create `.env.example`**

File content:
```
GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json
```

- [ ] **Step 2: Verify it's NOT git-ignored (must be committable, unlike real .env)**

Run: `git check-ignore -v .env.example; echo "exit: $?"`
Expected: exit code 1 (no match — NOT ignored), no output line.

- [ ] **Step 3: Verify no real secret leaked in — diff against the real credentials.json content**

Run: `grep -c '"' .env.example` (real service-account JSON keys always contain quoted JSON fields; this file must have zero)
Expected: `0` (no double-quote characters — confirms it's a bare `KEY=value` line, not pasted JSON).

- [ ] **Step 4: Commit**

```bash
git add .env.example
git commit -m "feat(VDAP-193): add .env.example with placeholder GOOGLE_SERVICE_ACCOUNT_JSON"
```

---

## Self-Review

**1. Spec coverage:** Technical Steps = create `.env.example` with `GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json` → Step 1. AC = committed, no real secret → Steps 2-4. Covered, no gaps.
**2. Placeholder scan:** No TBD/TODO — the file's own placeholder value (`credentials.json`) is the intended content per the ticket, not a plan placeholder.
**3. Type consistency:** N/A (no code, single dotenv line).
