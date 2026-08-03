# VDAP-252 README Getting Started Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `README.md` with a "Getting Started" section that lets a new person clone the repo and run the pipeline without asking anyone anything.

**Architecture:** Single new file, `README.md`, containing one section. No code — this is a documentation-only ticket, so there is no TDD red/green cycle. Verification instead means literally following the written steps in a clean checkout and confirming they work end-to-end.

**Tech Stack:** Markdown.

## Global Constraints

- Technical Notes (VDAP-252, verbatim): clone repo → `cp .env.example .env` → điền `GOOGLE_SERVICE_ACCOUNT_JSON` → `uv sync` → run the pipeline.
- AC (verbatim): người mới làm theo đúng thứ tự chạy được pipeline không cần hỏi thêm.
- **Deviation from the ticket's literal example command, decided this session:** the ticket's Technical Notes show `uv run main.py --layer all --run-date <date>`, but `--layer`/`--run-date` is Phase 3 scope (bd `vietdist-analytics-platform-a9l.8`, "P3.8 CLI Orchestration", still `open` — not implemented). `main.py` (VDAP-236/242) takes no arguments today. Writing the ticket's literal command would make a new person's first command fail, directly violating this ticket's own AC. The README documents the command that actually works today (`uv run main.py`), with a one-line note that `--layer`/`--run-date` lands in Phase 3.
- Scope: `README.md` gets exactly one section, "Getting Started" — no other sections (architecture overview, contributing, etc.) unless a later ticket asks for them (YAGNI).
- No `pyproject.toml`/`main.py`/`.env.example` changes — this ticket only adds `README.md`.

---

### Task 1: Write `README.md`

**Files:**
- Create: `README.md`

**Interfaces:**
- Produces: nothing consumed by other tickets — this is a leaf documentation deliverable.

- [x] **Step 1: Write `README.md`**

```markdown
# VietDist Analytics Platform

## Getting Started

1. Clone the repo:
   ```bash
   git clone <repo-url>
   cd vietdist-analytics-platform
   ```

2. Copy the environment template and fill in your Google Service Account key path:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `GOOGLE_SERVICE_ACCOUNT_JSON` to the path of your `credentials.json` (default: `credentials.json` in the repo root). Place the actual `credentials.json` file (provided separately — never commit this file) at that path.

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Run the pipeline:
   ```bash
   uv run main.py
   ```
   You should see log lines like:
   ```
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] pipeline run started
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] placeholder layer running
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] OK: 1/1 nguồn thành công ở layer=bronze
   2026-08-03 12:00:00,000 [INFO] [batch_id=...] pipeline run finished
   ```
   and exit code `0`.

   > `--layer`/`--run-date` CLI flags (e.g. `uv run main.py --layer all --run-date 2026-08-03`) are planned for Phase 3 (P3.8) and not available yet — today's `main.py` runs a fixed placeholder bronze layer.
```

- [x] **Step 2: Verify end-to-end in a clean checkout** — cloned to /tmp/vdap-readme-check, copied README.md + credentials.json (both untracked/gitignored so `git clone` alone doesn't carry them, matching what a real new dev must also do manually), ran cp .env.example .env → uv sync (installed cleanly) → uv run main.py → got the exact 4 log lines shown in the README, exit code 0

Run (from a scratch directory, not this working copy, so nothing here masks a missing step):
```bash
rm -rf /tmp/vdap-readme-check
git clone /Users/anhtran/Desktop/vietdist-analytics-platform /tmp/vdap-readme-check
cd /tmp/vdap-readme-check
cp .env.example .env
cp /Users/anhtran/Desktop/vietdist-analytics-platform/credentials.json .
uv sync
uv run main.py
echo "exit code: $?"
```
Expected: dependencies install cleanly, `main.py` prints the 4 log lines shown in the README, exit code `0`. If any step fails or needs a command not written in the README, the README has a gap — fix it and re-verify.

- [x] **Step 3: Clean up the scratch checkout** — `rm -rf /tmp/vdap-readme-check`, confirmed gone

```bash
rm -rf /tmp/vdap-readme-check
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs(VDAP-252): add Getting Started section to README"
```

---

## Self-Review

**1. Spec coverage:** Technical Notes (clone → .env.example → uv sync → run) → Task 1 Step 1, in that exact order. AC (new person runs it without asking) → Task 1 Step 2's clean-checkout verification is the direct proof of this, not just re-reading the file. Deviation on the `--layer`/`--run-date` example command → documented in Global Constraints and in the README's own note, so it isn't silently wrong.
**2. Placeholder scan:** `<repo-url>` is a real placeholder a reader fills in with their actual remote — that's normal README convention, not an unfinished plan step. No TBD/TODO.
**3. Type consistency:** N/A — no code, no shared signatures across tasks (single task, single file).
