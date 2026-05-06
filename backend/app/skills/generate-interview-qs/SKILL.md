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
1. **获取用户背景** — db_read("user_profiles") 拿到技能标签、项目经历、工作经历，同时获取关联的 JD 信息作为补充
2. **生成全面覆盖的面试问题** — 基于步骤1的信息，按 references/question-types.md 的分类生成6-8道题：
   - 项目深挖：项目中的技术决策、难点解决、架构思考
   - 工作经历复盘：工作内容的深度和广度、成长路径
   - 技术基础：技能标签对应的核心技术点
   - 行为面试：团队协作、冲突处理、推动能力
   每道题分配唯一 id（q1， q2， ...），附上 type（题型）、focus（考察点）和 tips（回答方向提示），answer 和 feedback 初始为 null
3. **写入面试记录** — db_write("interviews"， data = {application_id, questions: [{id, question, type, focus, tips, answer: null, feedback: null}], overall_feedback: null, weaknesses: [], status: "in_progress"})

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
