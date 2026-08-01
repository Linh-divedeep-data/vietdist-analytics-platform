# Workspace Setup — thứ tự cài đặt tools & skills

> File này để Claude (hoặc cậu) chạy lại toàn bộ setup khi init một workspace mới.
> Cứ nói với Claude: **"làm theo WORKSPACE_SETUP.md"**.

Có 2 nhóm:
- **A. Global (1 lần / máy)** — cài đặt cấp máy, dùng cho mọi workspace.
- **B. Per-workspace (mỗi project)** — chạy bên trong thư mục project mới.

---

## Yêu cầu trước (prerequisites)

| Tool | Kiểm tra | Cài |
|------|----------|-----|
| Homebrew | `brew --version` | https://brew.sh |
| Node ≥ 20.19 | `node -v` | `brew install node` |
| pipx | `pipx --version` | `brew install pipx && pipx ensurepath` |
| Claude Code CLI | `claude --version` | đã có |

---

## A. Global — cài 1 lần cho máy

Các bước này an toàn khi chạy lại (đã cài thì báo "already installed").

```bash
# 1) beads — issue tracker (bd) + dependency dolt
brew install beads

# 2) code-review-graph — MCP review graph
pipx install code-review-graph            # hoặc: pipx upgrade code-review-graph

# 3) OpenSpec — spec-driven workflow (cli: openspec)
npm install -g @fission-ai/openspec@latest

# 4) caveman — plugin trả lời ngắn, tiết kiệm output token (scope: user)
npx -y github:JuliusBrussee/caveman -- --only claude --non-interactive

# 5) karpathy-guidelines — plugin nguyên tắc coding (scope: user)
claude plugin marketplace add multica-ai/andrej-karpathy-skills
claude plugin install andrej-karpathy-skills@karpathy-skills
```

> Plugin caveman + karpathy cài scope **user** → tự động có ở mọi workspace,
> không cần lặp lại ở bước B.

---

## B. Per-workspace — chạy trong project mới

Đứng ở **thư mục gốc project**, chạy theo thứ tự:

```bash
# 1) beads — khởi tạo issue tracker cho project (tạo .beads/)
bd init

# 2) superpowers — bộ skills (writing-plans, TDD, systematic-debugging,
#    git-worktrees, code-review, ...) → cài vào .agents/skills/, symlink Claude Code
npx --yes skills add obra/superpowers

# 3) code-review-graph — cấu hình cho Claude Code (.mcp.json, hooks,
#    skills, chèn hướng dẫn vào CLAUDE.md, git pre-commit hook)
code-review-graph install --platform claude-code
code-review-graph build          # build knowledge graph

# 4) OpenSpec — khởi tạo spec workspace (tạo openspec/, skills, commands
#    cho Claude Code + Codex)
openspec init
```

### 5) .gitignore — bỏ qua file local

Đảm bảo `.gitignore` có các mục sau (một số bước ở trên tự thêm):

```gitignore
# macOS
.DS_Store

# Logs
*.log

# Local machine-specific config
.claude/settings.local.json
.codex/config.local.toml

# Beads / Dolt
.dolt/
*.db
.beads-credential-key
.beads/proxieddb/

# code-review-graph
.code-review-graph/
```

---

## Sau khi xong

1. **Khởi động lại Claude Code / IDE** để nhận plugins, skills, MCP, slash commands.
2. Kiểm tra nhanh:
   ```bash
   bd version
   openspec --version
   code-review-graph --help
   claude plugin list        # thấy caveman@caveman, andrej-karpathy-skills@karpathy-skills
   ```
3. Slash commands có thể dùng: `/caveman`, `/opsx:propose "..."`.

---

## Ghi chú
- Thứ tự B quan trọng: `bd init` và `code-review-graph install` đều đụng vào
  `CLAUDE.md` / `.gitignore` — chạy đúng thứ tự để không xung đột.
- Muốn gỡ caveman: `npx -y github:JuliusBrussee/caveman -- --uninstall`.
- `code-review-graph build` cần chạy lại khi codebase đổi nhiều để cập nhật graph.
