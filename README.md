# Skill Audit Plugin

A Claude Code plugin that audits skills against a comprehensive 30-item quality checklist, runs comparative evaluations with and without the skill, proposes automated fixes, and generates detailed reports. The plugin helps maintain high-quality skills by catching common issues like missing sections, unclear instructions, incorrect triggers, and poor smoke test coverage, then validates improvements through multi-iteration eval testing.

## Installation

```bash
claude plugin add https://github.com/Mahima-Gujjarlapudi/skill-audit-plugin
```

## Quick Start (Verify Installation)

After installing, copy the included dummy skill into your project and audit it:

```bash
# Copy the example skill into your project's skills directory
cp -r <plugin-path>/examples/dummy-skill .claude/skills/hello-world

# Run the audit to verify everything works
/audit-skills hello-world --checklist-only
```

You should see a checklist score and report generated in `./skill-audit-output/`.

## Usage

### Main Commands

```bash
# Run full audit pipeline (checklist + eval + report)
/audit-skills <skill-name>

# Audit all skills in the workspace
/audit-skills --all

# Run checklist only (skip eval testing)
/audit-skills <skill-name> --checklist-only

# Run audit and auto-apply fixes
/audit-skills <skill-name> --fix

# Specify custom output directory
/audit-skills <skill-name> --output-dir ./reports
```

### Examples

```bash
# Audit the pdf-upload skill
/audit-skills pdf-upload

# Audit all skills and save reports to docs/audits/
/audit-skills --all --output-dir docs/audits

# Quick checklist for criteria-tree skill
/audit-skills criteria-tree --checklist-only

# Audit and auto-fix workspace-state skill
/audit-skills workspace-state --fix
```

## What It Checks

The plugin validates skills against a 30-item checklist across 7 categories:

### 1. File & Folder Setup (4 items)
- Skill definition file exists and is valid YAML
- Skill prompt file exists
- Skill is registered in index
- Folder structure follows conventions

### 2. Description Quality (5 items)
- Description is concise (1-2 sentences)
- Describes what the skill does, not how
- No implementation details in description
- Avoids jargon and acronyms
- Matches actual skill behavior

### 3. Instruction Quality (6 items)
- Instructions are clear and actionable
- Proper markdown formatting
- Examples provided where helpful
- Edge cases documented
- No contradictory instructions
- Instructions match description

### 4. Required Sections (5 items)
- Has Purpose/Overview section
- Has Parameters/Inputs section
- Has Output/Returns section
- Has Error Handling guidance
- Has Next Steps or Follow-up section

### 5. Trigger Accuracy (4 items)
- Trigger patterns match skill name
- Triggers capture all valid use cases
- No overly broad triggers
- Triggers don't conflict with other skills

### 6. Registration (3 items)
- Listed in skills index/README
- Category assignment is appropriate
- No duplicate registrations

### 7. Smoke Tests (3 items)
- At least 3 smoke test prompts defined
- Tests cover main use cases
- Tests include edge cases

## The Pipeline

The audit pipeline runs in 10 stages:

1. **Load Skill**: Read skill definition, prompt file, and registration data
2. **Run Checklist**: Validate all 30 checklist items, generate pass/fail/skip results
3. **Generate Test Prompts**: Create 3 prompts covering typical use, edge cases, and error scenarios
4. **Baseline Eval**: Run prompts WITHOUT the skill, record pass/fail for assertions
5. **With-Skill Eval**: Run prompts WITH the skill enabled, record pass/fail
6. **Compare Results**: Calculate delta (with_skill% - without_skill%), flag regressions
7. **Propose Fixes**: Generate fixes for failed checklist items (add sections, clarify instructions, etc.)
8. **Apply Fixes** (if `--fix` flag): Auto-apply proposed fixes to skill files
9. **Re-eval** (if fixes applied): Run iteration 2 eval to measure improvement
10. **Generate Report**: Create markdown report with checklist, eval results, grade, and recommendations

## Output

Each audit generates multiple output files:

### Markdown Report
```
<output-dir>/<skill-name>-audit-report.md
```
Human-readable report with:
- Executive summary (grade, pass rate, key issues)
- Checklist results (30 items with pass/fail/skip)
- Eval comparison table (with vs without skill)
- Fixes applied (if any)
- Iteration 2 results (if fixes applied)
- Recommendations for manual review

### HTML Report
```
<output-dir>/audit-report.html
```
Cumulative HTML report containing all audited skills in a single page with sidebar navigation. Updated automatically each run. Generated via `generate-report.py` (stdlib-only Python, no pip dependencies).

### Raw JSON
```
<output-dir>/<skill-name>-audit-data.json
```
Machine-readable data for CI/CD integration:
- Checklist results array
- Eval prompts and assertions
- Pass rates and deltas
- Fixes applied
- Final grade

## Requirements

- **Claude Code CLI**: Version 1.0.0 or higher
- **Python 3.10+**: (optional) For HTML report generation — stdlib only, no pip install needed
- **Git**: For detecting skill changes and generating diffs

## Output Directory

Default: `./skill-audit-output/`

Override with `--output-dir <path>`. Each audit run updates the cumulative `audit-report.html` and `audit-data.json` in this directory.

## Grading Scale

- **A (90-100%)**: Excellent — all critical items pass, high eval delta
- **B (80-89%)**: Good — minor issues, positive eval delta
- **C (70-79%)**: Acceptable — some issues, small eval impact
- **D (60-69%)**: Needs work — multiple failures, negligible eval benefit
- **F (<60%)**: Failing — critical issues, negative eval delta or regressions

## CI/CD Integration

Exit codes:
- `0`: Audit passed (grade B or higher, no regressions)
- `1`: Audit failed (grade D or F, or regressions detected)
- `2`: Audit error (skill not found, invalid YAML, etc.)

Example GitHub Actions workflow:

```yaml
- name: Audit Skills
  run: |
    for skill in $(ls .claude/skills/); do
      /audit-skills $skill --output-dir ./audit-reports
    done

- name: Upload Reports
  uses: actions/upload-artifact@v3
  with:
    name: skill-audit-reports
    path: ./audit-reports/
```

## Contributing

See `CONTRIBUTING.md` for guidelines on adding new checklist items, eval patterns, and fix generators.

## License

MIT License - see LICENSE file for details

## Support

- Issues: https://github.com/Mahima-Gujjarlapudi/skill-audit-plugin/issues
- Docs: https://github.com/Mahima-Gujjarlapudi/skill-audit-plugin/wiki
- Changelog: https://github.com/Mahima-Gujjarlapudi/skill-audit-plugin/blob/main/CHANGELOG.md
