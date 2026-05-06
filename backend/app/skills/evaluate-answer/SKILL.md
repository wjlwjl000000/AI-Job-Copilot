---
name: evaluate-answer
description: Use when a simulated interview session ends or the user explicitly requests evaluation, and a queue of answered questions needs batch scoring, gap analysis, and persistence as an Interview record. Also use when the user wants overall interview performance feedback.
---

# Evaluate Answer

## Overview
Batch-evaluate all answered interview questions from the session queue, score each against the rubric, identify cross-question weakness patterns, persist the Interview record, and provide feedback. Scoring criteria in `references/evaluation-rubric.md`.

## When to Use
- User says "结束面试" or "评估我的回答" after answering one or more questions
- Interview Agent's question queue has answered items and session is complete
- User explicitly requests overall interview performance summary

## When NOT to Use
- Questions generated but not yet answered → `generate-interview-qs`
- Individual question feedback during Q&A → Agent handles inline during session
- Queue is empty → ask user to answer at least one question first

## Workflow
1. **获取完整问答队列** — read_qa_queue() 获取所有 Q&A 对
2. **逐一评估队列中的每道回答** — 对照 references/evaluation-rubric.md 的标准，从三个维度分析：
   - 准确性：技术要点是否正确、无事实错误
   - 完整性：是否覆盖了问题期望的关键点
   - 清晰度：逻辑结构是否连贯、表达是否简洁
   每题给出 0-10 评分和具体反馈
3. **识别跨题弱项模式** — 汇总所有题目的评估结果，找出反复出现的薄弱领域（如"系统设计类问题连续3题得分<6"），标记为 weaknesses
4. **写入面试记录** — db_write("interviews", {
     application_id,
     questions: [{question, answer, feedback: {score, strengths, gaps}}],
     overall_feedback,
     weaknesses: [{topic, suggestion}]
   })
4. **整体表现不佳时给予鼓励** — 如果平均分 < 5 或 weaknesses ≥ 3 个 → call_support_agent(trigger="interview_fail") 获取经历分享，嵌入最终反馈

> 步骤1和2在Agent的Thought阶段自然完成，不需要call_llm工具。

## Output Format
```
{
  "questions": [{
    "question": "面试问题原文",
    "answer": "用户回答原文",
    "feedback": {
      "score": "0-10整数评分",
      "strengths": ["回答中的优点"],
      "gaps": ["缺失的关键点"]
    }
  }],
  "overall_feedback": "整体评价"（肯定整体表现、指出主要弱项方向、给出改进优先级）,
  "weaknesses": [{"topic": "弱项领域", "suggestion": "改进建议"}],
  "avg_score": "平均分"
}
```

## Common Mistakes
- Evaluating individual answers during Q&A phase → batch-evaluate only when session ends
- Forgetting to persist via db_write → Interview record must be saved
- Overly critical tone without acknowledging strengths → feedback must balance praise and critique
- Skipping weakness pattern analysis → cross-question trends are more valuable than per-question scores alone
