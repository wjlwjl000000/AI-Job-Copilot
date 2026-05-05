---
name: score-match
description: 当用户想了解简历与某个岗位的匹配程度、存在待评估的简历-JD对时使用。
---

# 简历-职位匹配度评估

## 目标
评估简历与目标JD的多维度匹配度。

## 工作流程
1. 使用 db_read 获取画像和JD数据
2. 使用 call_llm 从技能、经验、学历、薪资四个维度对比
3. 生成评分报告 + 差距项 + 改进建议

## 输出格式
{"overall": float, "skill_match": float, "experience_match": float, "education_match": float, "strengths": [...], "gaps": [...], "suggestions": [...]}

## 关联
- overall < 0.6 → 加载 optimize-resume
- overall < 0.6 → 调 call_support_agent
