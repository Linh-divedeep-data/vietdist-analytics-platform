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
| `ci` | `ci(VDAP-24): make pytest --collect-only step fail-safe` |
| `docs` (no ticket) | `docs: revert branch-workflow base back to develop` |

`refactor` is also a valid type (no commit of this type exists in this repo yet) — use `refactor(VDAP-<key>): ...` for changes that restructure code without changing behavior.

`hotfix`/`bugfix` branch types are part of the convention above but have no commit history in this repo yet — when used, follow the same `fix(VDAP-<key>): ...` commit format shown for `fix` above.

## Pull requests

Title: same format as commits — `<type>(VDAP-<key>): <imperative summary>`.

Body: two sections, `## Summary` (bullet points of what changed) and `## Test plan` (checklist of what was verified).
