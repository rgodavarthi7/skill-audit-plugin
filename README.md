# Skill Audit

A Claude Code custom slash command that audits skills and commands against a 30-item quality checklist, runs comparative evaluations (with vs without the skill), proposes automated fixes, and generates HTML metric reports.

## Installation

Clone this repo and copy two files into your project:

```bash
# Clone the repo (one time)
git clone https://github.com/rgodavarthi7/skill-audit-plugin.git

# Copy the slash command into your project
mkdir -p <your-project>/.claude/commands
cp skill-audit-plugin/commands/audit-skills.md <your-project>/.claude/commands/

# Copy the HTML report generator (optional, requires Python 3.10+)
cp skill-audit-plugin/generate-report.py <your-project>/
```

That's it. The `/audit-skills` command is now available in any Claude Code session inside your project.

## Quick Start

```bash
# Open Claude Code in your project
cd <your-project>
claude

# Audit a specific skill or command
/audit-skills my-skill-name

# Audit all skills/commands in the project
/audit-skills --all

# Quick checklist only (no eval agents)
/audit-skills my-skill-name --checklist-only
```

## Usage

```bash
/audit-skills <skill-name>                # Full audit pipeline
/audit-skills --all                       # Audit all skills/commands
/audit-skills <name> --checklist-only     # Skip eval testing
/audit-skills <name> --fix               # Auto-apply proposed fixes
/audit-skills <name> --force             # Re-run even if recent report exists
/audit-skills <name> --output-dir ./path # Custom output directory
```

## What It Checks

30-item checklist across 7 categories:

| Category | Items | Type |
|----------|-------|------|
| File & Folder Setup | 4 | AUTO |
| Description Quality | 5 | AUTO + LLM |
| Instruction Quality | 6 | AUTO + LLM |
| Required Sections | 5 | AUTO |
| Trigger Accuracy | 4 | LLM |
| Registration | 3 | AUTO |
| Smoke Tests | 3 | EXEC |

- **AUTO**: Programmatic checks (file exists, frontmatter valid, grep for sections)
- **LLM**: Judgment-based (clarity, trigger specificity, relevance)
- **EXEC**: Execution-based (smoke tests, agent spawning) — skipped with `--checklist-only`

## The Pipeline

1. **Discovery** — Find skill files via glob patterns
2. **Checklist Scoring** — Score against 30-item standard
3. **Test Prompt Generation** — Create baseline + failure-targeted prompts with 6 assertions each
4. **Parallel Eval** — With-skill vs without-skill agent comparison
5. **Fix Generation** — Propose edits grouped by root cause
6. **Apply Fixes + Re-test** — Verify previously-failing prompts
7. **Full Re-test** — Catch regressions
8. **Convergence Loop** — Iterate up to 3x until stable
9. **Report Generation** — Markdown + JSON + cumulative HTML

## Output

Default directory: `./skill-audit-output/`

| File | Description |
|------|-------------|
| `{name}-audit.md` | Markdown report with checklist, eval results, grade |
| `{name}-eval.json` | Machine-readable eval data for CI/CD |
| `audit-data.json` | Cumulative manifest (all audited skills) |
| `audit-report.html` | Combined HTML dashboard — one file, all skills, sidebar nav |
| `SUMMARY.md` | Aggregate table (--all mode only) |

The HTML report updates incrementally — re-auditing a skill replaces its entry, auditing a new skill appends it.

## Grading Scale

| Grade | Range | Meaning |
|-------|-------|---------|
| A | 90-100% | Excellent — all critical items pass, high eval delta |
| B | 80-89% | Good — minor issues, positive eval delta |
| C | 70-79% | Acceptable — some issues, small eval impact |
| D | 60-69% | Needs work — multiple failures, negligible eval benefit |
| F | <60% | Failing — critical issues, negative eval delta or regressions |

## HTML Report Generator

The `generate-report.py` script converts eval JSON to a styled HTML dashboard. Stdlib-only Python, no pip dependencies.

```bash
# Generate report from eval data
python generate-report.py ./skill-audit-output/audit-data.json -o ./skill-audit-output/audit-report.html

# Read from stdin
cat audit-data.json | python generate-report.py -

# Single skill JSON (object) or multiple skills (array) both work
```

## Requirements

- **Claude Code CLI** (any recent version)
- **Python 3.10+** (optional) — only for HTML report generation, stdlib only

## License

MIT License - see LICENSE file for details

## Support

- Issues: https://github.com/rgodavarthi7/skill-audit-plugin/issues
