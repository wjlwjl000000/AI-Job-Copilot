---
name: match-jobs
description: Use when the user wants to discover real job openings matching their profile, needs skill-based career recommendations, or the system proactively suggests new positions after profile updates or application rejections.
---

# Match Jobs

## Overview
Search external job platforms using the user's profile (skills, target role, location, salary preference) and return a ranked list with match scores and recommendation reasons.

## When to Use
- User says "帮我搜职位" or "有什么适合我的"
- Profile just built and initial recommendations needed
- After application rejection, proactively match new opportunities
- User wants to explore positions in a new direction

## When NOT to Use
- Specific JD needs scoring → `score-match`
- Resume needs optimization → `optimize-resume`

## Workflow
1. **获取搜索条件** — db_read("user_profiles") 拿到技能标签、目标岗位、期望城市、薪资范围
2. **联网搜索职位** — web_search(目标岗位 + 技能关键词 + 城市, source="boss") 从外部招聘平台搜索当前开放的职位
3. **匹配评分并推荐** — 对搜索结果逐条分析：
   - 提取 JD 中的 requirements（技能要求 + 等级 + 是否必须）
   - 将用户技能标签与 requirements 逐项对比，计算技能重合度
   - 结合城市、薪资匹配度、经验年限要求，给出 0-1 综合匹配分
   - 按分数排序，每题生成一句话推荐理由（解释匹配点和差距点）

> 步骤3在Agent的Thought阶段自然完成，不需要call_llm工具。web_search 返回的原始结果需要 Agent 提取和格式化。

## Output Format
```
{
  "matches": [{
    "job_id": "平台职位ID",
    "source": "boss | lagou | manual",
    "jd_content": "职位描述原文",
    "requirements": [{"skill": "技能名", "level": "要求等级", "required": true}],
    "company": "公司名",
    "salary_range": "薪资范围",
    "city": "城市",
    "score": "0-1综合匹配度",
    "reason": "匹配理由"（技能重合度与差距点的一句话概述）
  }]
}
```

## Common Mistakes
- 只搜不评分 → 每条 JD 必须与用户画像对比产生 score
- requirements 不全 → 需要提取 JD 中隐含的技能要求
- 忽略城市和薪资过滤 → 搜索和排序时优先考虑用户偏好
