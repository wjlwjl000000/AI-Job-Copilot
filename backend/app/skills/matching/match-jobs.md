---
name: match-jobs
description: Use when the user wants to discover job openings that fit their profile, needs skill-based career recommendations, or the system proactively suggests positions after profile changes or application rejections.
---

# 职位匹配搜索

## 概述
基于用户画像向量语义搜索匹配职位，返回排序列表和推荐理由。

## When to Use
- 用户说"帮我搜职位""有什么适合我的"
- 画像刚构建完成，需要初始推荐
- 被拒后主动匹配新机会

## When NOT to Use
- 指定 JD 需要打分 → `score-match`
- 搜索公司信息 → `web_search`

## 工作流程
1. **db_read**("user_profiles") → 获取技能上下文
2. **chroma_query**("jobs", profile_summary, k=10) → 语义搜索
3. **call_llm**(matches + profile) → 排序 + 生成推荐理由

## 输出格式
```json
{"matches": [{"job_id": "...", "title": "...", "company": "...", "score": 0.85, "reason": "..."}]}
```

## 常见错误
- chroma_query collection 写成 "profiles" → 应为 "jobs"
- 只返回分数不加理由 → call_llm 生成可读推荐语
