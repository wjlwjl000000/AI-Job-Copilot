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
1. **获取完整问答队列** — read_qa_queue(interview_id="iv-xxx") 获取所有 Q&A 对
2. **逐一评估** — 对照 references/evaluation-rubric.md 从准确性/完整性/清晰度三个维度评分(0-10)，在Thought阶段完成
3. **识别跨题弱项** — 汇总评估结果找出反复出现的薄弱领域，标记为weaknesses
4. **持久化** — db_write(table="interviews", data={questions: [...含feedback...], overall_feedback, weaknesses, status: "completed"}, record_id="iv-xxx")
5. **低分鼓励** — avg_score<5 或 weaknesses≥3 → call_support_agent(trigger="interview_fail", context={avg_score, weaknesses})

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

## Examples

### 示例1：批量评估
**工具调用**：
1. read_qa_queue(interview_id="iv-001") → [{id, question, answer}, ...]
2. Thought：逐题从准确性/完整性/清晰度评分(0-10)，识别跨题弱项
3. db_write(table="interviews", data={questions: [...含feedback...], overall_feedback, weaknesses, status: "completed"}, record_id="iv-001")

### 示例2：低分触发鼓励
**工具调用**：
1. read_qa_queue(interview_id="iv-001") → [...]
2. Thought评估 → avg_score=4.2
3. call_support_agent(trigger="interview_fail", context={avg_score: 4.2, weaknesses: [...]})
4. db_write(table="interviews", data={..., status: "completed"}, record_id="iv-001")

> 评分在Thought阶段完成。avg_score<5或weaknesses≥3时必须调用call_support_agent。update操作必须传record_id。