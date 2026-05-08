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
1. db_read(table="applications") → 统计各状态数量
2. chroma_query(collection="jobs", query=目标岗位+城市, k=3) → 今日匹配
3. chroma_query(collection="stories", query="daily motivation") → 激励语
4. call_llm(prompt=stats+matches+story) → 100字内播报

## Output Format
```json
{"stats": {"applied": 5, "screening": 2, "interview": 1, "offer": 0}, "daily_matches": [...], "motivation": "..."}
```

## Common Mistakes
- Inaccurate stats → always db_read actual data
- Report too long → keep body under 100 characters

## Examples

### 示例1：每日求职播报
**工具调用**：
1. db_read(table="applications") → 统计各status计数
2. chroma_query(collection="jobs", query="AI工程师 北京", k=3) → [{title, company, score}, ...]
3. chroma_query(collection="stories", query="daily motivation") → [{content: "..."}]
4. call_llm(prompt="汇总stats+matches+story为100字以内的播报")

> stats由db_read返回的实际记录统计得出，不得编造数字。motivation通过call_llm生成，≤100字。
