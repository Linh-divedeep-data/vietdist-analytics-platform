# VDAP-171 Data/Src/Tests Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the base directory skeleton (`data/{raw,bronze,silver,gold}`, `src/`, `tests/`) so later ingestion/pipeline code has somewhere to read/write without `FileNotFoundError`.

**Architecture:** Pure filesystem scaffolding — `mkdir -p` for the tree, one `.gitkeep` per otherwise-empty directory so git tracks them (git does not track empty dirs).

**Tech Stack:** shell/filesystem only.

## Global Constraints

- Exact dirs required (Technical Steps, VDAP-171): `data/raw`, `data/bronze`, `data/silver`, `data/gold`, `src`, `tests`
- AC: `ls data/` shows all 4 data subdirs.

---

### Task 1: Create skeleton directories with .gitkeep

**Files:**
- Create: `data/raw/.gitkeep`
- Create: `data/bronze/.gitkeep`
- Create: `data/silver/.gitkeep`
- Create: `data/gold/.gitkeep`
- Create: `src/.gitkeep`
- Create: `tests/.gitkeep`

**Interfaces:**
- Consumes: nothing
- Produces: directory tree that VDAP-172+ (config/ + src/extract/ package skeleton) and later Bronze ingestion tickets will populate with real files.

- [ ] **Step 1: Create the directory tree**

Run: `mkdir -p data/raw data/bronze data/silver data/gold src tests`
Expected: exit code 0, no output.

- [ ] **Step 2: Add `.gitkeep` to each empty dir (git doesn't track empty dirs)**

Run: `touch data/raw/.gitkeep data/bronze/.gitkeep data/silver/.gitkeep data/gold/.gitkeep src/.gitkeep tests/.gitkeep`
Expected: exit code 0.

- [ ] **Step 3: Verify the AC**

Run: `ls data/`
Expected output: `bronze`, `gold`, `raw`, `silver` (4 entries).

- [ ] **Step 4: Confirm git will track the new dirs**

Run: `git status --short`
Expected: 6 new untracked `.gitkeep` files under `data/*/`, `src/`, `tests/`.

- [ ] **Step 5: Commit**

```bash
git add data/raw/.gitkeep data/bronze/.gitkeep data/silver/.gitkeep data/gold/.gitkeep src/.gitkeep tests/.gitkeep
git commit -m "feat(VDAP-171): create data/{raw,bronze,silver,gold}, src/, tests/ skeleton"
```

---

## Self-Review

**1. Spec coverage:** Technical Steps = `mkdir -p data/{raw,bronze,silver,gold} src tests` + `.gitkeep` → Task 1 Steps 1-2 cover both. AC = `ls data/` shows 4 subdirs → Step 3. Covered, no gaps.
**2. Placeholder scan:** No TBD/TODO — every step is a real command.
**3. Type consistency:** N/A (no code, filesystem only).
