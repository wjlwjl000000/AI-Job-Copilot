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

## Data Models

### user_profiles（读）
| 字段 | 类型 | 含义 |
|------|------|------|
| skill_tags | JSON | 技能标签：[{name, level}] |
| target | JSON | 求职目标：{cities, salary_range, roles} |
| work_years | INT | 工作年限 |

### web_search 返回的职位数据（非数据库表）
| 字段 | 类型 | 含义 |
|------|------|------|
| job_id | STR | 职位在平台的ID |
| source | STR | 来源："boss"|"lagou"|"manual" |
| jd_content | TEXT | JD原文 |
| requirements | JSON | 技能要求：[{skill, level, required}] — 由Agent从jd_content中提取 |
| company | STR | 公司名 |
| salary_range | STR | 薪资范围 |
| city | STR | 城市 |

## Examples

### 示例1：按技能和城市搜索匹配职位
**场景**：用户画像已构建，说"帮我找北京的AI工程师岗位"。

**工具调用序列**：
1. db_read("user_profiles") → [{skill_tags: [{"name": "Python","level": "高级"},{"name": "FastAPI","level": "中级"},{"name": "Docker","level": "初级"}], target: {cities: ["北京"], salary_range: "25k-35k", roles: ["AI工程师"]}}]

2. web_search("AI工程师 Python FastAPI 北京", source="boss") → [
     {title: "AI应用开发工程师", jd: "负责AI产品后端开发，要求Python/FastAPI，3年以上经验...", company: "XX科技", salary: "20k-35k", city: "北京"},
     {title: "后端开发(AI方向)", jd: "...", company: "YY智能", salary: "30k-50k", city: "北京"}
   ]

3. 在Thought中对每条结果评分（不调用额外工具）——所有数据来自步骤1和2的返回值：
   - XX科技：技能重合3/3(Python/FastAPI/Docker), 城市匹配, 薪资在范围内, 年限满足 → score=0.85
   - YY智能：技能重合2/3(缺FastAPI), 薪资下限30k略高于期望25k, 年限要求5年>4年 → score=0.52

**最终输出**：
{
  "matches": [
    {"job_id": "boss-001", "source": "boss", "jd_content": "...", "requirements": [{"skill": "Python","level": "高级","required": true},{"skill": "FastAPI","level": "中级","required": true},...], "company": "XX科技", "salary_range": "20k-35k", "city": "北京", "score": 0.85, "reason": "技能高度重合，城市薪资均符合预期"},
    {"job_id": "boss-002", ..., "score": 0.52, "reason": "缺少FastAPI经验，薪资期望略低，年限要求偏高"}
  ]
}

### 示例2：搜索结果为空
**场景**：用户的城市和岗位组合无搜索结果。

**工具调用序列**：
1. db_read("user_profiles") → [{target: {cities: ["拉萨"], roles: ["AI工程师"]}}]
2. web_search("AI工程师 拉萨", source="boss") → []

3. 在Thought中判断：搜索为空，应告知用户并建议调整条件，不返回空列表了事

**最终输出**：
{
  "matches": [],
  "suggestion": "拉萨暂无AI工程师相关职位。建议：1) 扩大城市范围到成都、西安；2) 放宽到'后端开发'或'数据分析'方向。是否需要我按新条件重新搜索？"
}

> 示例中的字段值来自db_read和web_search返回的实际数据。requirements字段由Agent从jd_content中提取，不得编造不存在的技能要求。评分在Thought阶段完成，不调用额外工具。
