# Eval Output Schema

## eval-output.json

The eval pipeline produces a JSON file per skill with this structure:

```json
{
  "skill_name": "string",
  "skill_path": "string",
  "timestamp": "ISO 8601 datetime",
  "model": "string",
  "checklist": {
    "total": 30,
    "passed": "number",
    "failed": "number",
    "skipped": "number",
    "items": [
      {
        "number": 1,
        "text": "Folder uses lowercase-with-dashes",
        "category": "File and Folder Setup",
        "type": "AUTO|LLM|EXEC",
        "status": "PASS|FAIL|SKIP",
        "reason": "string (explanation)"
      }
    ]
  },
  "eval": {
    "iterations": [
      {
        "iteration": 1,
        "note": "Before fixes | After fixes",
        "prompts": [
          {
            "id": "baseline-1",
            "text": "The test prompt text",
            "type": "baseline|failure-targeted",
            "targets_item": null | 18,
            "results": {
              "with_skill": {
                "response_summary": "Brief summary of response",
                "assertions": [
                  {
                    "id": "A1",
                    "text": "References correct command",
                    "verdict": "PASS|FAIL",
                    "evidence": "Brief quote or explanation"
                  }
                ],
                "pass_count": 5,
                "total": 6,
                "duration_seconds": 42.3,
                "token_count": 11400
              },
              "without_skill": {
                "response_summary": "Brief summary",
                "assertions": [...],
                "pass_count": 2,
                "total": 6,
                "duration_seconds": 83.1,
                "token_count": 31000
              }
            }
          }
        ],
        "aggregate": {
          "with_skill": {
            "pass_rate": 0.94,
            "total_assertions": 18,
            "passed": 17,
            "avg_duration": 41.2,
            "avg_tokens": 11200
          },
          "without_skill": {
            "pass_rate": 0.28,
            "total_assertions": 18,
            "passed": 5,
            "avg_duration": 82.5,
            "avg_tokens": 30500
          },
          "delta": "+66%"
        }
      }
    ]
  },
  "fixes": [
    {
      "iteration": 1,
      "changes": [
        {
          "section": "Related Skills",
          "action": "add",
          "description": "Added Related Skills section linking to validate-tree and submit-review"
        }
      ]
    }
  ],
  "skill_creator_eval": {
    "available": true|false,
    "results": "object or null (plugin-specific metrics)"
  },
  "summary": {
    "grade": "A|B|C|D|F",
    "pre_fix_score": "22/30",
    "post_fix_score": "28/30",
    "with_skill_pass_rate": "94%",
    "without_skill_pass_rate": "28%",
    "delta": "+66%",
    "unresolved_items": []
  }
}
```

## Audit Report Format (Markdown)

The markdown report follows this structure:

```markdown
# Skill Audit: `{name}`

**File:** `.claude/skills/{name}/SKILL.md` | **Score:** {pass}/{total}
**Generated:** {date} | **Model:** {model}

---

## Checklist Results

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | ... | PASS | |

## What's Wrong
(numbered list of failures)

## What's Good
(positive findings)

---

## Eval Results (Iteration 1 - Before Fixes)

**Prompt 1:** "..."
| Assertion | With Skill | Without Skill |
|-----------|-----------|--------------|
| ... | PASS | FAIL |

### Aggregate
| Metric | With Skill | Without Skill | Delta |
|--------|-----------|--------------|-------|
| Pass Rate | X% | Y% | +Z% |

---

## Fixes Applied
(numbered list)

---

## Eval Results (Iteration 2 - After Fixes)
(same format as iteration 1, with-skill only)

---

## Iteration Comparison
| Metric | Iter 1 | Iter 2 | Change |
|--------|--------|--------|--------|

## Skill-Creator Plugin Results
(if available)
```
