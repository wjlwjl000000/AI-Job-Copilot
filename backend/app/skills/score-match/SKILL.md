---
name: score-match
description: Use when the user wants to evaluate how well their resume matches a specific JD, when a resume-JD pair needs multi-dimensional scoring, or when the user asks about their fit for a target role.
---

# Score Match

## Overview
Multi-dimensional evaluation of resume-to-JD match across skills, experience, education, and salary, producing a weighted overall score with gap analysis and actionable suggestions. Detailed rubric in `references/scoring-dimensions.md`.

## When to Use
- User says "我和这个岗位匹配吗" or "评估一下匹配度"
- `build-profile` completed and user wants to check fit for a JD in `user_profiles.jd`
- `match-jobs` found positions and user wants detailed scoring on specific ones

## When NOT to Use
- No JD available in profile → ask user to provide JD first
- No resume/profile built → `parse-resume` or `build-profile` first
- Just need general job search → `match-jobs`

## Workflow
1. **获取简历和 JD** — db_read("user_profiles") 拿技能标签、工作年限、教育背景、期望薪资，同时获取 jd 字段中的 JD 内容和 requirements
2. **多维度对比评分** — 从四个维度逐一分析：
   - 技能重合度：逐项对比 profile.skill_tags 与 jd.requirements 中的技能要求，计算匹配率，标注缺失技能
   - 经验匹配度：对比工作年限和岗位方向与 JD 中隐含的经验要求
   - 学历匹配度：对比 education.degree 与 JD 的学历要求
   - 薪资匹配度：对比 profile.target.salary_range 与 JD 的薪资范围
   综合四个维度得出 0-1 总分（overall）
3. **生成差距分析和建议** — 对每个缺失项给出具体改进建议，标注哪些是 JD 标记为 required 的硬性要求
4. **低分时触发关联动作** — overall < 0.6 → call_support_agent(trigger="low_match") 获取鼓励；如有可优化点且用户未明确拒绝 → 建议使用 `optimize-resume`

> 步骤2-4在Agent的Thought阶段自然完成。评分细则参考 references/scoring-dimensions.md。

## Output Format
```
{
  "overall": "0-1综合匹配分"（四维度加权平均）,
  "skill_match": "0-1技能重合度"（匹配的技能数/JD要求的技能数）,
  "experience_match": "0-1经验匹配度",
  "education_match": "0-1学历匹配度",
  "salary_match": "0-1薪资匹配度"（期望薪资在JD范围内的程度）,
  "strengths": ["匹配较好的点"],
  "gaps": ["不匹配的具体技能或条件"],
  "suggestions": ["针对每个差距的具体改进建议"]
}
```

## Common Mistakes
- Scoring without cross-referencing jd.requirements → must compare each requirement
- Missing call_support_agent when score < 0.6 → low match triggers encouragement
- JD not in user_profiles.jd → check this field, not jobs table

## Data Models

### user_profiles（读）
| 字段 | 类型 | 含义 |
|------|------|------|
| skill_tags | JSON | 技能标签：[{name, level}] |
| work_years | INT | 工作年限 |
| education | JSON | 学历：{degree, school, major} |
| target | JSON | 期望：{salary_range} |
| jd | JSON | 目标JD：{content: "JD原文", requirements: [{skill, level, required}]} |

## Examples

### 示例1：完整多维匹配评分
**场景**：用户问"我和XX科技的AI工程师岗位匹配吗"，profile.jd中已有该JD。

**工具调用序列**：
1. db_read("user_profiles") → [{skill_tags: [{"name": "Python","level": "高级"},{"name": "FastAPI","level": "中级"},{"name": "Docker","level": "初级"}], work_years: 4, education: {degree: "本科", major: "计算机科学"}, target: {salary_range: "25k-35k"}, jd: {content: "JD原文...", requirements: [{"skill": "Python","level": "高级","required": true},{"skill": "FastAPI","level": "中级","required": true},{"skill": "Kubernetes","level": "中级","required": false}]}}]

2. 在Thought中逐维度评分（不调用额外工具，所有数据来自步骤1返回值）：
   - 技能重合度：3项中匹配2项(Python/FastAPI)，缺Kubernetes（非必须项，权重降低）→ 0.78
   - 经验匹配度：JD隐含要求3-5年，用户4年 → 0.85
   - 学历匹配度：JD要求本科，用户本科 → 1.0
   - 薪资匹配度：JD范围20k-35k，用户期望25k-35k → 0.90
   - overall加权平均 → 0.73（>0.6，不触发call_support_agent）

**最终输出**：
{
  "overall": 0.73,
  "skill_match": 0.78,
  "experience_match": 0.85,
  "education_match": 1.0,
  "salary_match": 0.90,
  "strengths": ["Python/FastAPI与JD要求匹配", "学历符合", "经验年限在范围内"],
  "gaps": ["缺少Kubernetes经验（非必须项）"],
  "suggestions": ["Kubernetes是加分项，建议2周内通过在线课程补上基础概念并在简历中体现"]
}

### 示例2：低匹配度触发鼓励
**场景**：用户问"我和这个高级架构师岗位匹配吗"，差距较大。

**工具调用序列**：
1. db_read("user_profiles") → [{skill_tags: [{"name": "Python","level": "中级"}], work_years: 2, jd: {requirements: [{"skill": "系统架构设计","level": "专家","required": true},{"skill": "团队管理","level": "高级","required": true}]}}]

2. 在Thought中逐维度评分 → overall=0.32，严重低于0.6

3. call_support_agent(trigger="low_match", context={overall: 0.32, target_role: "高级架构师", key_gap: "经验年限和架构设计能力"}) → {story: "...", encouragement: "...", source: "user_contributed"}

**最终输出**：{overall: 0.32, ..., gaps: ["经验年限差距大(2年 vs 8年要求)", "缺少架构设计经验"], suggestions: ["建议先从高级工程师入手，积累2-3年后再冲击架构师"], encouragement: {story: "...", encouragement: "之前有位2年经验的候选人从高级工程师做起，2年后成功晋升架构师...", source: "user_contributed"}}

> 示例中的字段值来自db_read和call_support_agent返回的实际数据。评分在Thought阶段完成，无需额外工具。overall<0.6必须调用call_support_agent。
