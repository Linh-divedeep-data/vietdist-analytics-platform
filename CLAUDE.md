# Project Instructions for AI Agents

This file provides instructions and context for AI coding agents working on this project.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->

## Ticket Branch Workflow

Khi bắt đầu 1 bd ticket mới (chưa có branch sẵn cho ticket đó):

```bash
git checkout main
git pull origin main
git checkout -b feature/<ticket-id>-<slug>   # branch từ main mới nhất
bd update <ticket-id> --claim
```

Rules:
- Repo chỉ còn 1 branch nền tảng là `main` (đã xóa `develop` và toàn bộ nhánh cũ) — luôn branch từ `main` mới nhất, không branch từ nhánh feature khác đang dở.
- Nếu đang làm branch cũ dở (đã claim từ trước), KHÔNG cần pull/branch lại — chỉ áp dụng khi bắt đầu ticket mới.
- Nếu có local change chưa commit khi checkout main, `git status` trước, stash nếu cần — không `checkout` đè mất việc đang làm.
- Đặt tên branch theo convention hiện có trong repo: `feature/<ID>-<slug>` (xem `git branch -a`).

### Naming convention bắt buộc (mọi lần tạo nhánh mới hoặc push)

Trước khi `git checkout -b` hoặc `git push -u origin <branch>`, kiểm tra tên branch khớp pattern:

```
<type>/<TICKET-ID>-<slug>
```

- `type` ∈ `feature`, `chore`, `hotfix`, `bugfix` (theo prefix đã dùng trong repo — xem `git branch -a`)
- `TICKET-ID` dạng `VDAP-<số>` (hoặc slug lowercase nếu chưa có ticket, ví dụ `vdap-0gd-...`)
- `slug` lowercase, cách nhau bằng dấu `-`, không khoảng trắng/ký tự hoa

Nếu tên branch không khớp pattern trên: KHÔNG tạo/push — báo lại cho user và hỏi tên đúng trước khi thực hiện.

### PR description convention

Title bắt buộc theo Conventional Commits + Jira key, khớp `type` dùng trong commit convention (`feat`/`fix`/`docs`/`chore`/`ci`/`refactor`/`test`):

```
<type>(VDAP-<key>): <tóm tắt ở dạng mệnh lệnh>
```

Body dùng 2 section chuẩn (theo mẫu `gh pr create` hiện có):

```
## Summary
- ...

## Test plan
- [ ] ...
```

Nếu title/body không khớp format trên: sửa lại trước khi `gh pr create`, không tạo PR sai convention.

## Build & Test

_Add your build and test commands here_

```bash
# Example:
# npm install
# npm test
```

## Architecture Overview

_Add a brief overview of your project architecture_

## Conventions & Patterns

_Add your project-specific conventions here_

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes_tool` or `query_graph_tool` instead of Grep
- **Understanding impact**: `get_impact_radius_tool` instead of manually tracing imports
- **Code review**: `detect_changes_tool` + `get_review_context_tool` instead of reading entire files
- **Finding relationships**: `query_graph_tool` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview_tool` + `list_communities_tool`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
| ------ | ---------- |
| `detect_changes_tool` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context_tool` | Need source snippets for review — token-efficient |
| `get_impact_radius_tool` | Understanding blast radius of a change |
| `get_affected_flows_tool` | Finding which execution paths are impacted |
| `query_graph_tool` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes_tool` | Finding functions/classes by name or keyword |
| `get_architecture_overview_tool` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes_tool` for code review.
3. Use `get_affected_flows_tool` to understand impact.
4. Use `query_graph_tool` pattern="tests_for" to check coverage.
