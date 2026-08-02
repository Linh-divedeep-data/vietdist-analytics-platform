# VDAP-205 CI Lint+Test Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `.github/workflows/ci.yml` so every push/PR runs `uv sync` + a lint pass + a placeholder test-collection step, catching syntax/import errors before they sit unnoticed on a branch.

**Architecture:** Single GitHub Actions workflow, one job, four steps (checkout, `astral-sh/setup-uv`, `uv sync`, lint via `uvx ruff check .`, then `uv run pytest --collect-only` as the placeholder test step — this last step is also what VDAP-210 formally verifies next).

**Tech Stack:** GitHub Actions, `astral-sh/setup-uv@v6`, `uvx` (ephemeral tool run, no permanent dependency added).

## Global Constraints

- Technical Notes (VDAP-205, verbatim): `.github/workflows/ci.yml`, dùng `astral-sh/setup-uv` action.
- Technical Steps: checkout → setup-uv → `uv sync` → `uv run ruff check .` (hoặc lint đơn giản) → placeholder test step.
- Design decision: use `uvx ruff check .` instead of `uv run ruff check .` — `ruff` is NOT a `pyproject.toml` dependency and this ticket is skeleton-only (adding a permanent lint dependency is out of scope); `uvx` runs it ephemerally without touching `pyproject.toml`. The ticket's own Technical Steps explicitly permit "hoặc lint đơn giản" as the alternative.
- AC: workflow file is valid YAML; appears in the repo's Actions tab when pushed.
- Trigger: `push` and `pull_request` on any branch (VDAP-202 Story AC scenario 1: "Given push lên branch bất kỳ").

---

### Task 1: Create the CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `pyproject.toml`/`uv.lock` (from VDAP-170)
- Produces: a `ci` workflow + `lint-test` job name that VDAP-210 references when it adds the real `pytest --collect-only` verification step, and that Epic 3 (P3.7, VDAP's `test_scd2_valid_to`/`test_mart_sales_vs_target`) later wires real tests into.

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

File content:
```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6

      - name: Install dependencies
        run: uv sync

      - name: Lint
        run: uvx ruff check .

      - name: Test collection (placeholder — real tests land in Epic 3)
        run: uv run pytest --collect-only
```

- [ ] **Step 2: Validate YAML syntax**

Run:
```bash
uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "VALID YAML"
```
Expected: `VALID YAML`, exit code 0. (`pyyaml` ships as a transitive dep of `google-auth`/other installed packages — if this import fails, fall back to `python3 -c "import yaml..."` using system Python, or install `pyyaml` via `uv run --with pyyaml python -c ...` without touching `pyproject.toml`.)

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "feat(VDAP-205): add GitHub Actions CI workflow (lint + test placeholder)"
```

- [ ] **Step 4: Push and confirm the workflow appears in the Actions tab (AC)**

This step happens after `finishing-a-development-branch` pushes the branch — verify with:
```bash
gh run list --workflow=ci.yml --limit=3
```
Expected: at least one run listed for this branch (proves GitHub picked up the workflow file and it's not malformed enough to be silently ignored).

---

## Self-Review

**1. Spec coverage:** Technical Notes (`.github/workflows/ci.yml`, `setup-uv`) → Step 1. Technical Steps (checkout → setup-uv → uv sync → lint → placeholder test) → Step 1's job steps in order. AC (valid YAML, visible in Actions) → Steps 2 and 4. Covered, no gaps.
**2. Placeholder scan:** No TBD/TODO in the YAML — the "placeholder" wording in the step name is the ticket's own required terminology (Technical Steps literally says "placeholder test step"), not an unfinished plan step.
**3. Type consistency:** N/A (YAML config, no functions/types). Job name `lint-test` is the one identifier future tickets (VDAP-210) need to reference — noted in Interfaces above.
