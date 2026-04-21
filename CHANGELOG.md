# Changelog

## [2.0.0] - 2026-04-21

### Changed
- Restructured from fake plugin format to Claude Code custom slash command
- Install is now: copy `commands/audit-skills.md` into `.claude/commands/`
- Moved `generate-report.py` to repo root for easy copying
- Rewrote README with correct installation and usage instructions

### Added
- `commands/audit-skills.md` — self-contained slash command with full 30-item checklist and pipeline
- `generate-report.py` at repo root (copy of `skills/audit-skills/references/generate-report.py`)

### Removed
- `.claude-plugin/plugin.json` and `marketplace.json` — these were fake; Claude Code has no plugin system

## [1.0.0] - 2026-04-20

### Added
- 30-item quality checklist across 7 categories
- 10-step eval pipeline with with-skill vs without-skill comparison
- Automated fix generation and convergence loop (max 3 iterations)
- HTML report generator (stdlib-only Python)
- Cumulative `audit-report.html` — one file updated across multiple audit runs
- Example eval JSON and dummy skill for testing
