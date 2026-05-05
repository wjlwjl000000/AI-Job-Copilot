---
name: comfort-user
description: Use when the user experiences rejection, low match scores, or interview failure and needs emotional support with RAG-retrieved similar job-seeking stories for personalized encouragement.
---

# Comfort User

## Overview
Retrieve similar job-seeking experiences via Chroma RAG and generate personalized encouragement. Results are always embedded in the caller's response, never delivered standalone. See `references/messaging-guide.md` for tone guidelines per trigger type.

## When to Use
- Match score < 0.6 → encouragement
- Application rejected → comfort + reframe
- Interview failed → reflection support
- Received offer → congratulations + story sharing
- New user onboarding → welcome message

## When NOT to Use
- No emotion-related trigger → don't proactively interrupt
- Technical analysis needed → `score-match` or `evaluate-answer`

## Workflow
1. **chroma_query**("stories", profile_summary + trigger) → similar experiences
2. **db_read**("user_profiles") → user context
3. **call_llm**(stories + profile + trigger) → encouragement:
   - Empathize first, then share story, end with constructive note
   - Keep under 200 characters

## Output Format
```json
{"story": "...", "encouragement": "...", "source": "crawled"}
```

## Rules
- Always return `state: "completed"` — never `input-required`
- Tone: warm, genuine, not preachy
- Results embedded in caller's return value

## Common Mistakes
- Generic platitudes → must reference specific chroma_query stories
- Triggering input-required → Support only returns completed
