# Skill Quality Checklist (30 Items)

Each item is scored PASS/FAIL/SKIP. Automation type: AUTO (programmatic), LLM (judgment), EXEC (execution).

## File and Folder Setup (4 items)

| # | Check | Type | How to Verify |
|---|-------|------|---------------|
| 1 | Folder uses lowercase-with-dashes | AUTO | Glob pattern match on folder name |
| 2 | Folder name matches `name:` field | AUTO | Read frontmatter, compare to dirname |
| 3 | File is called `SKILL.md` (exact case) | AUTO | Glob for SKILL.md in folder |
| 4 | YAML header opens/closes with `---` | AUTO | Regex on first lines |

## Description (5 items)

| # | Check | Type | How to Verify |
|---|-------|------|---------------|
| 5 | First sentence explains what skill does in plain English | LLM | Read description, judge clarity |
| 6 | Includes "Use when..." trigger phrases | AUTO | Grep for "Use when" or "use when" in description |
| 7 | Under 1,024 characters total | AUTO | Character count of description field |
| 8 | No angle brackets `<` or `>` | AUTO | Regex check on description |
| 9 | Does not trigger on unrelated requests | LLM | Test 5 off-topic prompts |

## Instructions (6 items)

| # | Check | Type | How to Verify |
|---|-------|------|---------------|
| 10 | Written as bullets/numbered steps, not paragraphs | LLM | Check formatting structure |
| 11 | Most important instructions at top | LLM | Judge ordering of content |
| 12 | Includes actual commands to run | AUTO | Grep for code blocks or backtick commands |
| 13 | Matches real project setup (no outdated tools/paths) | LLM | Cross-reference with project files |
| 14 | No hardcoded limits that belong in config | LLM | Check for magic numbers |
| 15 | Under 5,000 words (move detail to references/) | AUTO | Word count of SKILL.md body |

## Required Sections (5 items)

| # | Check | Type | How to Verify |
|---|-------|------|---------------|
| 16 | Has "What This Skill Does" section | AUTO | Grep for heading |
| 17 | Has "Examples" section with 2+ examples | AUTO | Grep for heading + count examples |
| 18 | Has "Error Handling" section | AUTO | Grep for heading |
| 19 | Has "Next Steps" section | AUTO | Grep for heading |
| 20 | Has "Related Skills" section | AUTO | Grep for heading |

## Trigger Testing (4 items)

| # | Check | Type | How to Verify |
|---|-------|------|---------------|
| 21 | Triggers on 10 different phrasings (9/10 target) | LLM | Generate 10 prompts, check trigger rate |
| 22 | Triggers on casual language rephrasing | LLM | Rephrase casually, check triggers |
| 23 | Does NOT trigger on 5 unrelated questions | LLM | Test 5 off-topic, verify no trigger |
| 24 | Has "Do NOT use for..." if over-triggers | AUTO | Check description for exclusion phrases (optional — only needed if 23 fails) |

## Registration (3 items)

| # | Check | Type | How to Verify |
|---|-------|------|---------------|
| 25 | Listed in agent file(s) under `.claude/agents/` | AUTO | Grep agent files for skill name (SKIP if no agents dir) |
| 26 | Has entry in `.claude/skills/README.md` | AUTO | Grep README for skill name (SKIP if no README) |
| 27 | Agent-to-skill mapping tables up to date | AUTO | Cross-reference agent declarations vs README (SKIP if either missing) |

## Smoke Test (3 items)

| # | Check | Type | How to Verify |
|---|-------|------|---------------|
| 28 | Normal input produces correct output | EXEC | Run skill with standard prompt |
| 29 | Bad/missing input fails gracefully | EXEC | Run skill with invalid input |
| 30 | 3 consecutive runs produce consistent format | EXEC | Run 3 times, compare structure |
