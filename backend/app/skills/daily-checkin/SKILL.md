---
name: daily-checkin
description: Use when the user signs in daily or the system triggers a periodic check-in, requiring a motivational summary with progress stats, new matches, and encouragement.
---

# Daily Checkin

## Overview
Generate a concise daily job-seeking report with stats, new opportunities, and motivation.

## When to Use
- User explicitly checks in
- System timer triggers (daily)
- User says "今天有什么新机会"

## When NOT to Use
- User is upset after rejection → `comfort-user`
- Just need job recommendations → `match-jobs`

## Workflow
1. **db_read**("applications") → stats
2. **chroma_query**("jobs", profile, k=3) → today's matches
3. **chroma_query**("stories", "daily motivation") → inspiration
4. **call_llm**(stats + matches + story) → report:
   - Numbers overview
   - Today's picks
   - One-sentence motivation

## Output Format
```json
{"stats": {"applied": 5, "screening": 2, "interview": 1, "offer": 0}, "daily_matches": [...], "motivation": "..."}
```

## Common Mistakes
- Inaccurate stats → always db_read actual data
- Report too long → keep body under 100 characters
