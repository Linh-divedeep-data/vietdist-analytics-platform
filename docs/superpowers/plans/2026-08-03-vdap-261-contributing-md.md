# VDAP-261 CONTRIBUTING.md Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `CONTRIBUTING.md` that writes down the branch and commit conventions this repo already follows, so git history stays traceable to Jira issue keys.

**Architecture:** Single new file, `CONTRIBUTING.md`, at repo root. Documentation-only — no TDD cycle. The content must match what this repo actually does (verified against real `git log` and `git branch` output and `CLAUDE.md`'s existing "Ticket Branch Workflow" section), not a newly-invented convention.

**Tech Stack:** Markdown.

## Global Constraints

- Technical Notes (VDAP-261, verbatim): branch strategy (`feature/VDAP-xx-slug`, `hotfix/VDAP-xx-slug`) + commit examples (`feat(VDAP-12): ...`, `fix(VDAP-20): ...`, `docs:`, `chore:`).
- AC (verbatim): file exists at repo root, with concrete examples for each type.
- Must match `CLAUDE.md`'s existing "Ticket Branch Workflow" section verbatim on: branch pattern `<type>/<TICKET-ID>-<slug>`, `type` ∈ `feature`/`chore`/`hotfix`/`bugfix`, `TICKET-ID` as `VDAP-<số>`.
- `feat`/`fix`/`docs`/`test`/`chore` examples must be real commits from this repo's `git log` (not invented) — `hotfix`/`bugfix` have no real commit history yet, so those are labeled as an allowed-but-not-yet-used convention, not "already used."
- No changes to any other file — this ticket only adds `CONTRIBUTING.md`.

---

### Task 1: Write `CONTRIBUTING.md`

**Files:**
- Create: `CONTRIBUTING.md`

**Interfaces:**
- Produces: nothing consumed by other tickets — leaf documentation deliverable.

- [x] **Step 1: Write `CONTRIBUTING.md`** — later added `ci`/`refactor` types too (found during Step 2 that CLAUDE.md's PR convention lists feat/fix/docs/chore/ci/refactor/test, not just the 5 I initially covered)

```markdown
# Contributing

## Branch naming

Pattern: `<type>/<TICKET-ID>-<slug>`

- `type` — one of: `feature`, `chore`, `hotfix`, `bugfix`
- `TICKET-ID` — the Jira key, e.g. `VDAP-42`
- `slug` — lowercase, words separated by `-`, no spaces or uppercase

Examples actually used in this repo:
- `feature/VDAP-205-ci-lint-test-workflow`
- `feature/VDAP-242-exit-code-summary-log`

Branch from `develop` (not `main` and not another in-progress feature branch) unless you're continuing work you already claimed.

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/): `<type>(VDAP-<key>): <imperative summary>` when the commit is tied to a ticket, or `<type>: <summary>` when it isn't.

| Type | Real example from this repo |
|---|---|
| `feat` | `feat(VDAP-242): exit non-zero + log ERROR summary when a layer has failures` |
| `fix` | `fix(VDAP-205): fix exit-code-5 handling broken by GitHub Actions' set -e shell` |
| `docs` | `docs(VDAP-252): add Getting Started section to README` |
| `test` | `test(VDAP-210): add placeholder import-coverage tests for src/ and config/` |
| `chore` | `chore(VDAP-25): add pip-audit security baseline` |
| `docs` (no ticket) | `docs: revert branch-workflow base back to develop` |

`hotfix`/`bugfix` branch types are part of the convention above but have no commit history in this repo yet — when used, follow the same `fix(VDAP-<key>): ...` commit format shown for `fix` above.

## Pull requests

Title: same format as commits — `<type>(VDAP-<key>): <imperative summary>`.

Body: two sections, `## Summary` (bullet points of what changed) and `## Test plan` (checklist of what was verified).
```

- [x] **Step 2: Verify against real history and CLAUDE.md** — confirmed every feat/fix/docs/test/chore/ci example is a real commit in `git log --all`; caught and fixed a real gap: CLAUDE.md lists `ci`/`refactor` as valid commit types too, which the first draft omitted

Run:
```bash
git log --oneline --all | grep -E "^\S+ (feat|fix|docs|test|chore)\(VDAP-[0-9]+\):" | head -5
```
Expected: at least one real match per type (`feat`, `fix`, `docs`, `test`, `chore`) confirming the table's examples are genuine commits, not invented ones. Cross-check each example string in `CONTRIBUTING.md` appears verbatim in this output or in `git log` history.

Then re-read `CLAUDE.md`'s "Ticket Branch Workflow" section and confirm `CONTRIBUTING.md`'s branch pattern/type list matches it exactly — no drift between the two documents.

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs(VDAP-261): add CONTRIBUTING.md with branch and commit conventions"
```

---

## Self-Review

**1. Spec coverage:** Technical Notes (branch strategy + commit examples for feat/fix/docs/chore) → Task 1 Step 1. AC (file exists, concrete examples per type) → same step, verified against real `git log` in Step 2. `hotfix`/`bugfix` explicitly called out as convention-not-yet-used, per this session's own honesty standard (no fabricated "already used" claim). No gaps.
**2. Placeholder scan:** No TBD/TODO. `<slug>`/`<TICKET-ID>`/`<key>` are documentation placeholders a contributor fills in — standard convention-doc notation, not unfinished plan content.
**3. Type consistency:** N/A — no code, single file, no shared signatures across tasks.
