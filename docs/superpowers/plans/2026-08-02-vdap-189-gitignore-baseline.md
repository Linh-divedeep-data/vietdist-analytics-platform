# VDAP-189 .gitignore Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `.gitignore` so pipeline output under `data/{raw,bronze,silver,gold}/` never gets committed, while the `.gitkeep` placeholders that keep those empty dirs in git (added in VDAP-171) stay tracked.

**Architecture:** Single-file edit. `credentials.json`/`.env`/`.venv/` etc. are already covered from earlier work — only the `data/*/*` glob + `.gitkeep` negation pattern is missing.

**Tech Stack:** `.gitignore` glob syntax only.

## Global Constraints

- Technical Steps (VDAP-189, verbatim): `.venv/, __pycache__/, .env, credentials.json, data/raw/*, data/bronze/*, data/silver/*, data/gold/* (giữ .gitkeep)`
- AC: `git check-ignore -v credentials.json` returns a match.
- Must not break `.gitkeep` tracking under `data/*/` (already committed in VDAP-171 — a gitignore change must not make git think they should be removed from tracking; git doesn't untrack already-committed files via `.gitignore` alone, but new files under `data/*/` must still be ignored except future `.gitkeep`s).

---

### Task 1: Add data/*/* patterns to .gitignore

**Files:**
- Modify: `.gitignore`

**Interfaces:**
- Consumes: nothing
- Produces: `.gitignore` blocking any new file under `data/raw/`, `data/bronze/`, `data/silver/`, `data/gold/` except `.gitkeep` — later Bronze/Silver/Gold write tickets (VDAP-92+) rely on this so `uv run pytest`/`git status` after a pipeline run doesn't show untracked Parquet output.

- [ ] **Step 1: Append the data-layer section to `.gitignore`**

Add this block (after the existing `# Secrets` section, before `# macOS`):
```gitignore
# Data lake output — keep folder structure (.gitkeep) but never commit data files
data/raw/*
data/bronze/*
data/silver/*
data/gold/*
!data/raw/.gitkeep
!data/bronze/.gitkeep
!data/silver/.gitkeep
!data/gold/.gitkeep
```

- [ ] **Step 2: Verify credentials.json is still ignored (AC)**

Run: `git check-ignore -v credentials.json`
Expected: `.gitignore:2:credentials.json	credentials.json` (unchanged from before this edit).

- [ ] **Step 3: Verify the new data/*/* patterns ignore real files but not .gitkeep**

Run:
```bash
touch data/raw/test_should_be_ignored.csv
git check-ignore -v data/raw/test_should_be_ignored.csv
git check-ignore -v data/raw/.gitkeep; echo "gitkeep check-ignore exit: $?"
rm data/raw/test_should_be_ignored.csv
```
Expected: first command matches (file ignored); second command exits 1 (NOT ignored — `.gitkeep` must stay trackable).

- [ ] **Step 4: Verify git status is clean of noise**

Run: `git status --short`
Expected: only `.gitignore` modified — no stray `data/*` entries appear as untracked.

- [ ] **Step 5: Commit**

```bash
git add .gitignore
git commit -m "feat(VDAP-189): extend .gitignore with data lake output patterns"
```

---

## Self-Review

**1. Spec coverage:** Technical Steps list `.venv/, __pycache__/, .env, credentials.json` (already present, untouched) + `data/*/*` patterns (Task 1). AC (`git check-ignore -v credentials.json` matches) verified in Step 2. Covered, no gaps.
**2. Placeholder scan:** No TBD/TODO — every step is a real command/diff.
**3. Type consistency:** N/A (no code).
