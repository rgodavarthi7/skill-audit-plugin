# Changelog

## [1.0.0] - 2026-04-20

### Added
- 30-item quality checklist across 7 categories (File Setup, Description, Instructions, Required Sections, Triggers, Registration, Smoke Tests)
- 10-step eval pipeline with with-skill vs without-skill comparison
- Automated fix generation and convergence loop (max 3 iterations)
- HTML report generator (`generate-report.py`) — stdlib-only Python, supports single and multi-skill reports
- Cumulative `audit-report.html` — one file updated across multiple audit runs
- `--all` mode for batch auditing all skills
- `--checklist-only`, `--fix`, `--force`, `--output-dir` flags
- Grading scale (A–F) with CI/CD exit codes
- Example eval JSON (`examples/sample-eval.json`)
- Example dummy skill (`examples/dummy-skill/`) for post-install smoke testing
