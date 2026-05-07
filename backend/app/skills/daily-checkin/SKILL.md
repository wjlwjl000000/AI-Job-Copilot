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

## Data Models

### applications（读）— db_read("applications")
| 字段 | 类型 | 含义 |
|------|------|------|
| status | STR | 状态："applied"|"screening"|"interview"|"offer"|"rejected" |

### jobs — chroma_query("jobs", ..., k=3) 返回
| 字段 | 类型 | 含义 |
|------|------|------|
| title | STR | 职位名称 |
| company | STR | 公司名 |
| score | FLOAT | 与画像的匹配度 |

### stories — chroma_query("stories", "daily motivation") 返回
| 字段 | 类型 | 含义 |
|------|------|------|
| content | TEXT | 激励故事或语录原文 |

## Examples

### 示例1：每日求职播报
**场景**：用户打开系统，系统触发每日签到。

**工具调用序列**：
1. db_read("applications") → [{status: "applied"}, {status: "applied"}, {status: "screening"}, {status: "interview"}, {status: "applied"}]（实际返回完整记录，Agent只统计各状态数量）

2. chroma_query("jobs", "AI工程师 北京", k=3) → [{title: "AI应用开发", company: "XX科技", score: 0.85}, {title: "后端开发(AI方向)", company: "YY智能", score: 0.72}, {title: "算法工程师", company: "ZZ数据", score: 0.60}]

3. chroma_query("stories", "daily motivation 求职") → [{content: "坚持就是胜利，每天进步一点点...", source: "crawled"}]

4. call_llm("汇总以下数据为一段100字左右的求职早报...") → "今日播报：5个进行中的申请（投递2/筛选1/面试1），3个新匹配职位。XX科技的AI应用开发岗匹配度85%，建议优先投递！坚持就是胜利。"

**最终输出**：
{
  "stats": {"applied": 3, "screening": 1, "interview": 1, "offer": 0},
  "daily_matches": [
    {"title": "AI应用开发", "company": "XX科技", "score": 0.85},
    {"title": "后端开发(AI方向)", "company": "YY智能", "score": 0.72}
  ],
  "motivation": "今日播报：5个进行中的申请，3个新匹配职位。XX科技的AI应用开发岗匹配度85%，建议优先投递！坚持就是胜利。"
}

> 示例中的字段值来自db_read和chroma_query返回的实际数据。stats中各状态数量通过统计db_read返回的实际记录得出，不得编造。motivation通过call_llm生成，需控制在100字以内。
