---
name: daily-checkin
description: Use when the user signs in daily or the system triggers a periodic check-in, and the agent needs to generate a motivational summary with progress stats, new opportunities, and encouragement.
---

# 每日签到

## 概述
生成求职日报：统计进展、推荐新机会、附上鼓励。

## When to Use
- 用户主动签到
- 系统定时触发（每天/每几天）
- 用户说"今天有什么新机会"

## When NOT to Use
- 用户遭遇挫折需要安慰 → `comfort-user`
- 仅需职位推荐 → `match-jobs`

## 工作流程
1. **db_read**("applications") → 统计投递数据
2. **chroma_query**("jobs", profile, k=3) → 今日新匹配
3. **chroma_query**("stories", "daily") → 励志故事
4. **call_llm**(stats + matches + stories) → 生成日报：
   - 数据概览（投递/面试/Offer 数）
   - 今日推荐
   - 一句话鼓励

## 输出格式
```json
{"stats": {"applied": 5, "screening": 2, "interview": 1, "offer": 0}, "daily_matches": [...], "motivation": "..."}
```

## 常见错误
- 统计数据不准 → 必须 db_read 实际数据
- 日报太长 → 简洁为主，不超过 100 字正文
