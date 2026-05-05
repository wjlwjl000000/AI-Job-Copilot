---
name: parse-resume
description: Use when a resume file (PDF, Word, TXT) is uploaded or attached, and structured fields like skills, experience, and education need to be extracted from the raw document.
---

# Parse Resume

## Overview
Extract structured data from uploaded resume files. Consumed by `build-profile` and `score-match`.

## When to Use
- User uploads a PDF / Word / TXT resume
- User says "看看我的简历" or "帮忙分析下"
- A new file attachment needs processing

## When NOT to Use
- Resume already parsed, need profile update → `build-profile`
- Need JD match scoring → `score-match`

## Workflow
1. **parse_document**(file_path) → raw text + metadata
2. **call_llm**(raw_text) → extract: name, education, experience, skills, projects
3. Missing critical fields (e.g. education) → return `state: "input-required"`

## Output Format
```json
{"raw_text": "...", "structured": {"skills": [...], "education": {...}, "experience": [...], "projects": [...]}}
```

## Common Mistakes
- Passing raw text directly as structured output → must call_llm first
- Skipping missing fields → return input-required, don't guess
