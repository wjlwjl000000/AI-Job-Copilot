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
