---
name: audit-skills
description: >
  Audit Claude Code skills against a 30-item quality checklist, generate test prompts,
  run with-skill vs without-skill comparisons, propose fixes, and produce audit reports.
  Use when auditing skill quality, testing skill improvements, benchmarking skills,
  running evals on skills, checking if skills trigger correctly, or measuring skill
  effectiveness. Also use when the user says "test my skill", "evaluate skill",
  "audit skill", "benchmark skill", or "check skill quality".
allowed-tools: Read, Write, Edit, Grep, Glob, Agent, Skill
---

# audit-skills

Automated skill quality audit pipeline with checklist scoring, eval testing, fix generation, and comprehensive reporting.

## What This Skill Does

Runs a 10-step pipeline to audit Claude Code skills:
1. **Discovery** — Find skills via glob patterns
2. **Checklist Scoring** — Score against 30-item quality standard (AUTO/LLM/EXEC checks)
3. **Test Prompt Generation** — Create baseline + failure-targeted prompts with assertions
4. **Run Test Prompts** — Parallel with-skill vs without-skill agent comparison
5. **Fix Generation** — Propose edits for failing items
6. **Apply Fixes + Re-test** — Apply edits and verify previously-failing prompts
7. **Full Re-test** — Run all prompts to catch regressions
8. **Convergence Loop** — Iterate up to 3 times until stable or unresolved
9. **Skill-Creator Eval** — Optional benchmark via plugin (if available)
10. **Report Generation** — Markdown + JSON output with scores and recommendations

## Usage

```bash
# Audit a single skill
/audit-skills pdf-upload

# Audit all skills in project
/audit-skills --all

# Checklist only (no eval agents)
/audit-skills run-tests --checklist-only

# Skip eval comparison (checklist + prompts only)
/audit-skills pdf-upload --skip-eval

# Auto-apply fixes without confirmation
/audit-skills pdf-upload --fix

# Force re-run even if recent report exists
/audit-skills pdf-upload --force

# Custom output directory
/audit-skills pdf-upload --output-dir docs/skills/audit/
```

## Pipeline Steps

### Step 0: Discovery

**Goal**: Find target skill(s) to audit

**Process**:
- If `--all`: `Glob(".claude/skills/*/SKILL.md")` to find all skills
- If single name: validate `<project-root>/.claude/skills/<name>/SKILL.md` exists
- Read SKILL.md content
- Extract frontmatter (name, description, allowed-tools, triggers)

**Output**: List of skill paths to audit

**Error Handling**:
- Skill not found → CRITICAL failure, exit with clear message
- Malformed frontmatter → Report as FAIL on checklist item 1, continue with partial data

### Step 1: Checklist Scoring

**Goal**: Score skill against 30-item quality standard

**Process**:
- Read checklist from reference file (or use embedded standard if plugin-only mode)
- For each item:
  - **AUTO** items: programmatic checks (file exists, frontmatter valid, etc.)
    - Use Glob to check file structure
    - Use Grep to check for required sections
    - Parse frontmatter YAML
  - **LLM** items: judgment-based (description clarity, trigger specificity)
    - Evaluate description quality
    - Check trigger patterns
    - Assess example relevance
  - **EXEC** items: requires execution (smoke tests, agent spawning)
    - Mark as SKIP if `--checklist-only`
    - Otherwise defer to Step 3 (eval prompts will test these)

**Output**: Structured results per item
```json
{
  "item_id": "C01",
  "category": "Core Requirements",
  "description": "SKILL.md exists at correct path",
  "type": "AUTO",
  "status": "PASS" | "FAIL" | "SKIP",
  "details": "Found at .claude/skills/pdf-upload/SKILL.md",
  "severity": "critical" | "major" | "minor"
}
```

**Scoring Logic**:
- PASS: 1 point
- FAIL: 0 points
- SKIP: excluded from denominator
- Final score: (PASS count) / (PASS + FAIL count) * 100

### Step 2: Test Prompt Generation

**Goal**: Create prompts to test skill behavior

**Process**:
- Generate 3 baseline prompts from skill description and examples
  - Extract use cases from "Use when..." text
  - Convert examples section into prompts
  - Generate variations of core skill purpose
- For each FAIL from Step 1, generate 1 failure-targeted prompt
  - Example: If "Examples section missing" → Create prompt that should trigger skill
  - Example: If "Trigger too broad" → Create prompt that should NOT trigger but might
- For each prompt, create 6 assertions (binary PASS/FAIL)
  - Assertions test skill-specific behaviors
  - Use reference templates for common patterns

**Prompt Template**:
```
Task: [User request that should trigger skill]

Context: [Minimal project context needed]

Expected Behaviors:
1. Skill is triggered correctly (assertion)
2. Required tools are used (assertion)
3. Output matches expected format (assertion)
4. Error handling works (assertion)
5. Documentation is updated if needed (assertion)
6. Result is validated before returning (assertion)
```

**Output**: List of test prompts with assertions
```json
{
  "prompt_id": "baseline_01",
  "type": "baseline" | "failure-targeted",
  "trigger_type": "explicit" | "implicit",
  "prompt_text": "...",
  "assertions": [
    {
      "id": "A1",
      "description": "Skill triggers correctly",
      "expected": "PASS"
    }
  ]
}
```

### Step 3: Run Test Prompts (Parallel)

**Goal**: Compare with-skill vs without-skill behavior

**Process**:
- For each prompt, spawn 2 agents in parallel:

  **With-skill agent**:
  ```
  Agent(type: "generic", context: {
    task: "Read the skill file at [path], then answer: [prompt]",
    instructions: "Use the skill if it applies. Follow skill instructions exactly."
  })
  ```

  **Without-skill agent**:
  ```
  Agent(type: "generic", context: {
    task: "[prompt]",
    instructions: "Answer from project context only. Do NOT read .claude/skills/."
  })
  ```

- Judge agent scores each response against assertions:
  ```
  Agent(type: "generic", context: {
    task: "Score this response against assertions",
    response: "[agent output]",
    assertions: [list],
    instructions: "Return JSON: {assertion_id: PASS|FAIL, reason: string}"
  })
  ```

- Cap concurrent agents at 4 total (2 test agents + 1 judge = 3 per prompt)
- Use agent timeout: 180 seconds per agent
- Retry once on timeout, then mark as SKIP

**Output**: Eval results per prompt
```json
{
  "prompt_id": "baseline_01",
  "with_skill": {
    "triggered": true,
    "response": "...",
    "assertions": {"A1": "PASS", "A2": "FAIL", ...},
    "score": 5.0
  },
  "without_skill": {
    "response": "...",
    "assertions": {"A1": "FAIL", "A2": "FAIL", ...},
    "score": 2.0
  },
  "delta": 3.0
}
```

**Key Metric**: Average delta across all prompts (with-skill score - without-skill score)
- Positive delta: skill adds value
- Zero/negative delta: skill ineffective or harmful

### Step 4: Fix Generation

**Goal**: Propose edits to address failures

**Process**:
- Collect all FAILs from Steps 1 (checklist) and 3 (eval)
- Group by root cause:
  - Missing sections → Add section
  - Vague description → Rewrite with specifics
  - Trigger too broad → Add negative examples
  - Missing error handling → Add error handling section
  - No examples → Generate examples from prompts
- For each group, generate Edit operation:
  ```json
  {
    "file_path": ".claude/skills/pdf-upload/SKILL.md",
    "old_string": "...",
    "new_string": "...",
    "rationale": "Fixes checklist item C03 (missing examples)"
  }
  ```
- Present fixes to user for approval (unless `--fix` flag)

**Fix Prioritization**:
1. Critical failures (file structure, frontmatter)
2. Major failures (missing core sections, broken triggers)
3. Minor failures (formatting, optional sections)

### Step 5: Apply Fixes + Re-test

**Goal**: Verify fixes resolve issues

**Process**:
- Apply approved edits via Edit tool
- Re-run ONLY previously-failing prompts (with-skill agents only)
- Compare iteration 2 results vs iteration 1
- Mark as RESOLVED if now PASS, otherwise UNRESOLVED

**Output**: Fix effectiveness report
```json
{
  "fix_id": "F01",
  "target": "C03 — Examples section missing",
  "applied": true,
  "resolved": true,
  "iteration_1_score": 0,
  "iteration_2_score": 1
}
```

### Step 6: Full Re-test

**Goal**: Catch regressions from fixes

**Process**:
- Re-run ALL prompts (baseline + failure-targeted)
- Compare iteration 2 vs iteration 1 for all prompts
- Flag any new failures (regressions)

**Regression Detection**:
- Any assertion that was PASS in iteration 1 but FAIL in iteration 2
- Report as WARNING with fix that caused regression

### Step 7: Convergence Loop

**Goal**: Iterate until stable or max iterations

**Process**:
- If new failures detected in Step 6:
  - Generate fixes (Step 4)
  - Apply + re-test (Step 5)
  - Full re-test (Step 6)
  - Increment iteration counter
- Loop max 3 times
- After 3 iterations, flag remaining failures as UNRESOLVED

**Exit Conditions**:
- All assertions PASS → SUCCESS
- No new failures in full re-test → STABLE
- Max iterations reached → UNRESOLVED

### Step 8: Skill-Creator Eval (Conditional)

**Goal**: Optional benchmark via skill-creator plugin

**Process**:
- Check if `skill-creator:skill-creator` skill is available
  - `Glob("**/.claude/skills/skill-creator/SKILL.md")` in parent dirs
  - Or check Claude Code plugin registry
- If available:
  - Invoke skill-creator eval API
  - Get description quality score
  - Get trigger optimization suggestions
- If not available:
  - Skip and note in report: "Install skill-creator plugin for advanced benchmarks"

**Output**: Optional benchmark data
```json
{
  "skill_creator_available": true,
  "description_score": 8.5,
  "suggestions": ["Add more negative examples", "Specify output format"]
}
```

### Step 9: Report Generation

**Goal**: Produce comprehensive audit report

**Process**:
- Generate markdown report at `./skill-audit-output/{name}-audit.md`
- Write JSON eval data to `./skill-audit-output/{name}-eval.json`
- Optionally generate HTML via external script (if available)

**Report Structure**:
```markdown
# Skill Audit Report: {skill-name}

**Date**: 2026-04-20
**Iterations**: 2
**Final Score**: 85.7% (24/28 items)

## Summary

- ✅ Core Requirements: 5/5
- ⚠️ Documentation: 6/8
- ✅ Behavior: 8/8
- ⚠️ Integration: 5/7

## Checklist Results

| ID | Category | Item | Status | Notes |
|----|----------|------|--------|-------|
| C01 | Core | SKILL.md exists | ✅ PASS | Found at .claude/skills/pdf-upload/SKILL.md |
| C02 | Core | Valid frontmatter | ✅ PASS | All required fields present |
...

## Eval Results

### Baseline Prompts

**Prompt 1**: "Upload a PDF policy document"
- With-skill: 6/6 assertions PASS
- Without-skill: 2/6 assertions PASS
- Delta: +4.0 (skill effective)

### Failure-Targeted Prompts

**Prompt 4**: "What happens if PDF is corrupted?"
- Iteration 1: 1/6 PASS (missing error handling)
- Iteration 2: 6/6 PASS (after fix F03)

## Fixes Applied

1. **F01** — Added examples section (resolves C03)
2. **F02** — Clarified trigger patterns (resolves C12)
3. **F03** — Added error handling documentation (resolves E15)

## Unresolved Issues

None — all failures resolved in 2 iterations.

## Recommendations

1. Consider adding more negative examples for trigger specificity
2. Add performance notes for large PDF files
3. Consider integration with policy-review workflow

## Next Steps

- Re-run audit after implementing recommendations: `/audit-skills pdf-upload --force`
- Install skill-creator plugin for description optimization
```

**JSON Schema**: See `references/schema.md` for full eval data structure

### Step 10: Summary (--all mode)

**Goal**: Aggregate report across all skills

**Process**:
- After auditing all skills, generate summary table
- Write to `./skill-audit-output/SUMMARY.md`
- Include links to individual reports

**Summary Table**:
```markdown
# Skill Audit Summary

**Date**: 2026-04-20
**Skills Audited**: 22/22

| Skill | Score | Status | Issues | Report |
|-------|-------|--------|--------|--------|
| pdf-upload | 85.7% | ✅ PASS | 4 resolved | [Link](pdf-upload-audit.md) |
| run-tests | 92.3% | ✅ PASS | 2 resolved | [Link](run-tests-audit.md) |
| validate-tree | 78.6% | ⚠️ WARN | 2 unresolved | [Link](validate-tree-audit.md) |
...
```

## Output Format

**Default Directory**: `./skill-audit-output/`
**Override**: `--output-dir <path>`

**Files Per Skill**:
- `{name}-audit.md` — Markdown report
- `{name}-eval.json` — Raw eval data (for HTML generation or external analysis)

**Global Files** (--all mode):
- `SUMMARY.md` — Aggregate results table
- `summary.json` — Machine-readable summary

## Error Handling

| Error | Handling |
|-------|----------|
| Skill file missing/malformed | Report as CRITICAL, skip remaining steps, mark skill as FAIL |
| Agent timeout | Retry once with 180s timeout, then mark assertion as SKIP |
| No checklist failures | Still run 3 baseline prompts (validate skill works as expected) |
| Fix causes regression | Convergence loop catches it in Step 6, reverts fix or iterates |
| All mode crash | Progress saved after each skill (crash-safe), resume from last completed |
| Output directory permission error | Fallback to `./tmp-skill-audit/`, warn user |

## Configuration

**Output**:
- Default directory: `./skill-audit-output/`
- Override: `--output-dir <path>`

**Convergence**:
- Max iterations: 3
- Exit on stable (no new failures)

**Concurrency**:
- Max concurrent agents: 4 (2 test + 1 judge + 1 buffer)
- Sequential skill processing in `--all` mode (parallelism within skill only)

**Optional Checks**:
- Agent registration: only if `.claude/agents/` exists
- Skills README: only if `.claude/skills/README.md` exists
- Skill-creator plugin: only if available in environment

## Examples

### Example 1: Audit a Single Skill

```
User: /audit-skills pdf-upload

Output:
🔍 Auditing skill: pdf-upload
✓ Step 0: Discovery — Found at .claude/skills/pdf-upload/SKILL.md
✓ Step 1: Checklist — 24/28 items PASS (85.7%)
⚠ Step 2: Generated 7 test prompts (3 baseline + 4 failure-targeted)
✓ Step 3: Eval — Avg delta +3.2 (skill effective)
⚠ Step 4: Generated 4 fixes for failing items
  📝 F01: Add examples section
  📝 F02: Clarify trigger patterns
  📝 F03: Add error handling docs
  📝 F04: Fix frontmatter format

Apply these fixes? [Y/n]: Y

✓ Step 5: Applied 4 fixes, re-testing...
✓ 3/4 issues resolved
⚠ Step 6: Full re-test — No regressions
✓ Step 7: Convergence — Stable after 2 iterations

📊 Final Score: 92.9% (26/28)
📄 Report: ./skill-audit-output/pdf-upload-audit.md
```

### Example 2: Checklist Only

```
User: /audit-skills run-tests --checklist-only

Output:
🔍 Auditing skill: run-tests (checklist only)
✓ Step 0: Discovery — Found
✓ Step 1: Checklist — 28/30 items PASS (93.3%)
  ❌ C15: Performance notes missing
  ❌ D08: Integration tests missing

⏭️ Skipping eval steps (--checklist-only)

📊 Final Score: 93.3%
📄 Report: ./skill-audit-output/run-tests-audit.md
```

### Example 3: Audit All Skills

```
User: /audit-skills --all

Output:
🔍 Auditing all skills...
Found 22 skills in .claude/skills/

[1/22] pdf-upload...        ✓ 85.7% (4 issues resolved)
[2/22] run-tests...          ✓ 92.3% (2 issues resolved)
[3/22] validate-tree...      ⚠ 78.6% (2 unresolved)
...
[22/22] deploy-backend...    ✓ 88.9% (3 issues resolved)

📊 Summary: 20/22 PASS, 2 WARN
📄 Reports: ./skill-audit-output/
📋 Summary: ./skill-audit-output/SUMMARY.md
```

## Checklist Items Reference

The 30-item checklist covers:

**Core Requirements (5 items)**:
- SKILL.md exists at correct path
- Valid frontmatter (name, description, allowed-tools)
- Description is clear and action-oriented
- Name follows kebab-case convention
- File size under 100KB

**Documentation (8 items)**:
- "What This Skill Does" section exists
- "Usage" section with examples
- "Examples" section with real prompts
- "Error Handling" section
- "Output Format" section
- "Related Skills" section
- No broken internal links
- Code examples are syntactically valid

**Behavior (8 items)**:
- Trigger phrases cover common variations
- Negative examples prevent false triggers
- Tool usage matches allowed-tools list
- Error handling is explicit
- Output is validated before returning
- User confirmation for destructive actions
- Progress updates for long operations
- Graceful degradation on tool failures

**Integration (7 items)**:
- Registered in SKILLS.md (if exists)
- References valid agent types (if agents exist)
- Cross-references other skills correctly
- No conflicts with other skill triggers
- Follows project conventions (if CLAUDE.md exists)
- Performance notes for expensive operations
- Migration notes for breaking changes

**Testing (2 items)**:
- Smoke test passes (skill can be invoked)
- Eval prompts all PASS with skill, some FAIL without

## Next Steps After Auditing

1. **Review the audit report** for failing items and unresolved issues
2. **Apply proposed fixes** (if not using `--fix` flag)
3. **Re-run audit** to verify fixes: `/audit-skills <name> --force`
4. **Install skill-creator plugin** (if available) for description optimization
5. **Update project documentation** if skill conventions changed
6. **Re-run in --all mode** to catch cross-skill conflicts

## Related Skills

- `skill-creator:skill-creator` — Create and optimize skill descriptions (optional external plugin)

## Notes

- **Project-agnostic**: Works in any Claude Code project, not just GMM Nexus
- **Crash-safe**: In `--all` mode, progress saved after each skill
- **No external dependencies**: Pure Claude Code tools (Read, Write, Edit, Grep, Glob, Agent, Skill)
- **Parallel execution**: Test prompts run concurrently (max 4 agents)
- **Convergence guarantee**: Max 3 iterations, then marks remaining as UNRESOLVED
- **Extensible**: Checklist items can be customized per project via reference file
