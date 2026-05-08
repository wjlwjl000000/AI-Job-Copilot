---
name: generate-interview-qs
description: Use when the user has an upcoming interview and needs targeted preparation questions based on their profile skills, project experience, and work history. Also use when an application enters the interview stage.
---

# Generate Interview Questions

## Overview
Generate comprehensive interview questions based on the user's profile (skills, projects, work experience), and persist them as an Interview record. Question type taxonomy in `references/question-types.md`.

## When to Use
- User says "帮我准备面试" or "面试会问什么"
- Application status enters "interview" stage
- User wants to practice for a specific company or role

## When NOT to Use
- User has answered all questions and wants evaluation → `evaluate-answer`
- No profile data available → ask user to provide background first
- Just need general interview tips → Agent handles conversationally

## Workflow
1. **获取用户背景** — db_read(table="user_profiles") 拿到技能标签、项目经历、工作经历，JD仅作补充
2. **生成面试问题** — 基于步骤1的信息，按 references/question-types.md 生成6-8道题覆盖四个类型，每题附id/type/focus/tips，answer和feedback初始为null
3. **写入面试记录** — db_write(table="interviews", data={application_id, questions: [...], overall_feedback: null, weaknesses: [], status: "in_progress"})

> 步骤2在Agent的Thought阶段自然完成。JD 仅作补充，不作为问题的主要来源。项目经历和工作经历是第一手素材。

## Output Format
```
{
  "interview_id": "iv-xxx",
  "questions": [{
    "id": "q1",
    "question": "面试问题",
    "type": "project_deep_dive | experience_review | technical | behavioral",
    "focus": "考察的具体能力点",
    "tips": "回答方向提示",
    "answer": null,
    "feedback": null
  }]
}
```

## Common Mistakes
- Only targeting weaknesses → questions should cover strengths as well
- Ignoring project and work experience → these are the richest question sources
- Questions without unique IDs → every question must have an id for answer tracking
- Forgetting to db_write → Interview record must be persisted

## Examples

### 示例1：基于简历生成面试问题
**工具调用**：
1. db_read(table="user_profiles") → {skills: [...], projects: [...], work_years: 4}
2. Thought：基于真实数据生成6-8道题（项目深挖/技术基础/工作经历/行为面试），每题附id/type/focus/tips
3. db_write(table="interviews", data={questions: [...], status: "in_progress"})

> 所有题目基于db_read返回的真实数据生成。answer和feedback初始必须为null。必须调用db_write持久化。
