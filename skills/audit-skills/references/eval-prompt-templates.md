# Eval Prompt Templates

## Baseline Prompts (generate 3 per skill)

### Template 1: Direct Request
Generate a prompt that directly asks for what the skill does, using natural language a real user would say.

Pattern: "I need to [action the skill performs]. [Optional context about what I'm working on]."

Example for a test-running skill: "I just changed the login flow. Can you run the tests to make sure nothing broke?"

### Template 2: Edge Case
Generate a prompt that tests an edge case or less obvious use of the skill.

Pattern: "[Unusual context or constraint]. [Request that should still trigger the skill]."

Example: "All my tests are failing after a merge conflict resolution. Can you help me figure out which ones are actually broken vs just need a rebuild?"

### Template 3: Error Scenario
Generate a prompt where something went wrong and the user needs the skill's error handling.

Pattern: "[Something failed or produced unexpected output]. [Request for help fixing it]."

Example: "The pytest run crashed with a segfault halfway through. How do I isolate which test caused it?"

## Failure-Targeted Prompts

For each failing checklist item, generate a prompt that would expose that specific failure:

| Failing Item | Prompt Pattern |
|---|---|
| Missing "Error Handling" section | "The [operation] failed with [error]. What do I do?" |
| Missing "Next Steps" section | "I just finished [skill action]. What should I do now?" |
| Missing "Related Skills" section | "After [skill action], what other tools should I use?" |
| Wrong commands | "Give me the exact command to [skill operation]" |
| Outdated paths | "Where is the [resource] located?" |
| Over-triggering | "[Completely unrelated request]" — assert skill does NOT trigger |
| Under-triggering | "[Casual rephrasing of skill action]" — assert skill DOES trigger |

## Assertion Patterns (6 per prompt)

Each assertion is a factual claim the response should satisfy:

1. **Command correctness**: "References the correct command/API/path for [operation]"
2. **Domain knowledge**: "Mentions [key concept] relevant to this operation"
3. **Guidance quality**: "Provides actionable next steps or troubleshooting"
4. **Cross-references**: "References related skills or documentation"
5. **Constraint adherence**: "Does not suggest [incorrect approach/tool]"
6. **Completeness**: "Covers [specific aspect] of the operation"

## Scoring Rules

- PASS: The assertion is clearly satisfied in the response
- FAIL: The assertion is clearly NOT satisfied
- Each assertion is independent (one FAIL doesn't affect others)
- Judge should provide brief evidence for each verdict
