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
git checkout develop
git pull origin develop
git checkout -b feature/<ticket-id>-<slug>   # branch từ develop mới nhất
bd update <ticket-id> --claim
```

Rules:
- `develop` là nhánh nền tảng để branch feature ra (tạo lại từ `main` ngày 2026-08-02 sau khi dọn sạch nhánh cũ) — luôn branch từ `develop` mới nhất, không branch từ `main` hay từ nhánh feature khác đang dở.
- Nếu đang làm branch cũ dở (đã claim từ trước), KHÔNG cần pull/branch lại — chỉ áp dụng khi bắt đầu ticket mới.
- Nếu có local change chưa commit khi checkout develop, `git status` trước, stash nếu cần — không `checkout` đè mất việc đang làm.
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

Body dùng template chuẩn sau (theo mẫu `gh pr create` hiện có) — mỗi PR phải trả lời được: tại sao làm, làm gì, làm như thế nào, và cách kiểm tra:

```
## Overview
- Lý do có thay đổi này, link ticket (Jira `VDAP-<key>` / bd issue id)

## Solution
- Mô tả ngắn cách giải quyết (API mới, sửa logic, update thư viện, ...)

## Changes
- File/module quan trọng đã sửa (gạch đầu dòng ngắn)

## How to test
- [ ] Bước để reviewer chạy thử / nghiệm thu

## Test plan
- [ ] ...
```

- `Overview`/`Solution`/`Changes`/`How to test` là section tối thiểu bắt buộc; `Test plan` giữ nguyên như checklist nghiệm thu hiện có, có thể gộp chung với `How to test` nếu nội dung trùng.
- Nếu thay đổi động tới UI/frontend/mobile: bắt buộc đính kèm screenshot hoặc GIF ngắn, ưu tiên dạng so sánh Before/After để reviewer thấy khác biệt không cần chạy code.

Nếu title/body không khớp format trên: sửa lại trước khi `gh pr create`, không tạo PR sai convention.

### Push + tạo PR xong → tự động bd close (không hỏi lại)

Ngay sau khi `git push` branch của 1 ticket + `gh pr create` chạy thành công (PR đã có URL trả về) — trong CÙNG lượt đó, chạy luôn `bd close <id>` cho ticket tương ứng. Không hỏi lại, không chờ duyệt riêng cho bước này — khác với chính sách "chờ duyệt" mặc định ở Conservative profile (Session Completion) chỉ áp dụng cho commit/push/PR, KHÔNG áp dụng cho `bd close` khi đã push+PR xong.

`bd close` sẽ tự tick Jira Done theo rule bên dưới (bd close → Jira Done).

Rules:
- Chỉ áp dụng khi push+PR thành công thật (có URL PR trả về, không lỗi). Push/PR lỗi thì KHÔNG bd close.
- Vẫn phải verify AC/test pass trước khi push (theo `verification-before-completion`) — quy tắc này chỉ bỏ bước hỏi lại cho `bd close`, không bỏ bước verify.
- Không mở rộng sang merge PR, force-push, hay bất kỳ thao tác git nào khác — những thao tác đó vẫn theo chính sách Conservative (chờ duyệt) trừ khi user nói rõ.

### bd close → Jira Done (tự động)

Bất kỳ lúc nào `bd close <id>` chạy cho 1 ticket có gắn Jira (field `External: jira-VDAP-<key>`) — dù lý do là PR đã tạo, AC đã verify xong không cần PR, hay dọn lại ticket cũ — ngay trong cùng lượt đó, chuyển luôn Jira issue tương ứng sang **Done** qua `getTransitionsForJiraIssue` + `transitionJiraIssue` (cloudId `87de12a7-0360-4035-9a5b-afdee4c28880`). Không hỏi lại. Nếu ticket không có field `External` trỏ Jira thì bỏ qua bước này.

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
