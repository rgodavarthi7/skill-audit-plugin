---
name: hello-world
description: >
  Greet the user and summarize the current project directory.
  Use when the user says "hello", "hi", "greet me", or "introduce yourself".
allowed-tools: Read, Glob
---

# hello-world

A minimal example skill for testing the audit pipeline.

## What This Skill Does

Reads the project root and returns a friendly greeting with a short summary of the top-level files and folders.

## Usage

```bash
/hello-world
```

## Examples

```
User: hello
Assistant: Hi! This project has 12 files across 3 directories. The main entry point is src/index.ts.
```

```
User: greet me
Assistant: Hello! I see a Python project with requirements.txt, setup.py, and 4 packages under src/.
```

## Error Handling

- If the project root is empty, respond: "This directory appears to be empty. Try running me inside a project."
- If Glob times out, respond: "I couldn't scan the directory. Please check file permissions."

## Next Steps

After greeting, suggest the user try:
1. `/audit-skills hello-world` to see an example audit report
2. Explore other available skills with `/help`

## Related Skills

- `audit-skills` — Audit any skill (including this one) against the 30-item quality checklist
