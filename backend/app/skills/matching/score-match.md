---
name: score-match
description: Use when the user asks how well their resume matches a specific job posting, or when the system detects a resume-JD pair that needs quantitative multi-dimensional evaluation.
---

# 匹配度评估

## 概述
从技能、经验、学历、薪资四个维度对比简历和目标 JD，输出评分和差距分析。

## When to Use
- 用户说"我和这个岗位匹配吗""这个岗位适合我吗"
- 系统自动评估（如投递前或面试前）
- Supervisor Planner 发出 `action: "score"` 任务

## When NOT to Use
- 只需要推荐职位列表 → `match-jobs`
- 已经知道匹配度低、只需优化 → 直接 `optimize-resume`

## 工作流程
1. **db_read**("user_profiles") + **db_read**("jobs", id) → 获取画像和 JD
2. **call_llm**(profile + jd) → 四维度对比：
   - 技能重合度（标签匹配 + 等级差异）
   - 经验匹配度（年限、岗位方向）
   - 学历匹配度（学历、专业）
   - 薪资匹配度（期望 vs JD 范围）
3. 输出评分 + strengths + gaps + suggestions

## 输出格式
```json
{"overall": 0.45, "skill_match": 0.5, "experience_match": 0.4, "education_match": 0.8, "strengths": [...], "gaps": [...], "suggestions": [...]}
```

## 关联
- overall < 0.6 → 加载 `optimize-resume`
- overall < 0.6 → 调用 **call_support_agent**(trigger="low_match")

## 常见错误
- 只看技能标签不看过往经验深度 → 对比需要多维
- 忘记触发 support → 低匹配时用户需要鼓励
