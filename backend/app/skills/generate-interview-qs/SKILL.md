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

## Data Models

### user_profiles（读）
| 字段 | 类型 | 含义 |
|------|------|------|
| skill_tags | JSON | 技能标签 |
| projects | JSON | 项目经验：[{name, description, tech_stack}] |
| work_years | INT | 工作年限 |
| jd | JSON | 目标JD：{content, requirements} — 仅作补充参考 |

### interviews（读/写）
| 字段 | 类型 | 含义 |
|------|------|------|
| id | UUID | 面试记录ID |
| application_id | UUID | 关联的投递ID（可为null） |
| questions | JSON | 题目列表：[{id, question, type, focus, tips, answer: null, feedback: null}] |
| overall_feedback | STR | 整体评价（评估后填充，生成阶段为null） |
| weaknesses | JSON | 弱项（评估后填充） |
| status | STR | "in_progress"（生成阶段）→ "completed"（评估后） |

## Examples

### 示例1：基于简历生成面试问题
**场景**：用户说"帮我准备面试，目标岗位是AI应用开发"。

**工具调用序列**：
1. db_read("user_profiles") → [{skill_tags: [{"name": "Python","level": "高级"},{"name": "FastAPI","level": "中级"},{"name": "Docker","level": "初级"}], projects: [{name: "智能客服系统", description: "基于LangChain的RAG客服机器人，日均处理5000+咨询", tech_stack: ["Python","LangChain","FAISS"]}], work_years: 4, jd: {content: "JD原文...", requirements: [...]}}]

2. 在Thought中生成6-8道题覆盖四个类型（不调用额外工具，所有信息来自步骤1）：
   - 项目深挖(2题)：基于projects字段中的"智能客服系统"
   - 技术基础(2题)：基于skill_tags中的Python高级/FastAPI中级/Docker初级
   - 工作经历(2题)：基于work_years=4年推断可能的工作场景
   - 行为面试(1题)：通用行为题

3. db_write("interviews", {user_id: "u-default", application_id: null, questions: [{id: "q1", question: "在智能客服系统中，你是如何设计LangChain Pipeline的？", type: "project_deep_dive", focus: "技术架构设计能力", tips: "建议从召回率、准确率两个维度说明优化思路", answer: null, feedback: null}, ...], overall_feedback: null, weaknesses: [], status: "in_progress"}) → {id: "iv-001"}

**最终输出**：
{
  "interview_id": "iv-001",
  "questions": [
    {"id": "q1", "question": "在智能客服系统中，你是如何设计LangChain Pipeline的？...", "type": "project_deep_dive", "focus": "技术架构设计能力", "tips": "建议从召回率、准确率两个维度说明优化思路", "answer": null, "feedback": null},
    {"id": "q2", "question": "Python中async/await的实现原理是什么？在你的项目中如何运用的？", "type": "technical", "focus": "Python异步编程理解深度", "tips": "可以结合FastAPI的异步特性来回答", "answer": null, "feedback": null},
    ...
    {"id": "q6", "question": "描述一次你遇到的最大的技术挑战及解决过程。", "type": "behavioral", "focus": "问题解决能力", "tips": "用STAR法则组织回答", "answer": null, "feedback": null}
  ]
}

> 示例中的所有数据来自步骤1的db_read返回值。题目内容基于用户真实的项目经历和技能生成，不得凭空编造用户没有的项目或技能。answer和feedback初始必须为null。
