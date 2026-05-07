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

## Data Models

### interviews — 通过 read_qa_queue()（读）和 db_write（写）
| 字段 | 类型 | 含义 |
|------|------|------|
| questions | JSON | 题目列表：[{id, question, type, answer, feedback: {score, strengths, gaps}}] |
| overall_feedback | STR | 整体评价 |
| weaknesses | JSON | 跨题弱项模式：[{topic, suggestion}] |
| status | STR | 评估完成后必须改为 "completed" |

## Examples

### 示例1：批量评估多道面试回答
**场景**：用户完成了3道模拟面试题的作答，说"评估我的回答"。

**工具调用序列**：
1. read_qa_queue() → [
     {id: "q1", question: "Python中async/await的实现原理？", answer: "async/await是基于协程的，本质上是事件循环机制...", type: "technical"},
     {id: "q2", question: "描述一次技术挑战", answer: "我们系统遇到高并发瓶颈，我引入了Redis缓存...", type: "behavioral"},
     {id: "q3", question: "你如何与产品经理协作？", answer: "我每周和PM对齐需求...", type: "behavioral"}
   ]

2. 在Thought中逐题评估（不调用额外工具，所有数据来自步骤1）：
   - q1：原理解释正确，提到了事件循环，未涉及Task/Future → 准确性7/完整性6/清晰度8 → score=7
   - q2：STAR结构清晰，有Redis具体措施，未说明优化效果量化 → 准确性8/完整性6/清晰度9 → score=7.5
   - q3：流程描述清楚，缺少具体冲突案例 → 准确性7/完整性5/清晰度8 → score=6.5
   跨题弱项：3题均存在"完整性不足"，缺少量化结果和边界条件

3. db_write("interviews", {id: "iv-001", questions: [{...含feedback...}], overall_feedback: "整体表现良好(均分7.0)。技术基础扎实，表达清晰。主要改进：每个技术点补充量化数据，行为面试用STAR法则，补充具体冲突案例。", weaknesses: [{topic: "回答完整性", suggestion: "每个技术点和案例补充量化指标（如性能提升百分比、处理请求量等）"}], status: "completed"})

**最终输出**：
{
  "questions": [
    {"question": "...", "answer": "...", "feedback": {"score": 7, "strengths": ["事件循环概念正确", "表达清晰"], "gaps": ["未涉及Task/Future概念", "缺少实际项目案例"]}},
    {"question": "...", "answer": "...", "feedback": {"score": 7.5, "strengths": ["STAR结构完整", "有Redis具体措施"], "gaps": ["未说明优化效果量化指标"]}},
    {"question": "...", "answer": "...", "feedback": {"score": 6.5, "strengths": ["协作流程描述清晰"], "gaps": ["缺少具体冲突处理案例"]}}
  ],
  "overall_feedback": "整体表现良好(均分7.0)。技术基础扎实，表达清晰。主要改进方向：每个技术点补充量化数据支撑，行为面试用STAR法则，补充具体的冲突/挑战案例。",
  "weaknesses": [{"topic": "回答完整性", "suggestion": "每个技术点和案例都要补充量化指标"}],
  "avg_score": 7.0
}

### 示例2：低分触发鼓励
**场景**：用户回答质量较差，均分<5，weaknesses≥3个。

**工具调用序列**：
1. read_qa_queue() → [3道题，回答质量均偏低]
2. 在Thought中评估 → avg_score=4.2, weaknesses≥3个
3. call_support_agent(trigger="interview_fail", context={avg_score: 4.2, weaknesses: ["技术基础薄弱","表达不清晰","缺少项目案例"]}) → {story: "...", encouragement: "第一次模拟面试不理想是正常的。之前有位候选人也经历了从均分3.5到均分8.0的提升...", source: "user_contributed"}
4. db_write("interviews", {..., status: "completed"})

**最终输出**：完整评估结果 + encouragement字段嵌入support agent返回的内容
（输出结构与示例1一致，但questions中各项score偏低，overall_feedback包含鼓励内容）

> 示例中的字段值来自read_qa_queue和call_support_agent返回的实际数据。评分在Thought阶段完成。avg_score<5或weaknesses≥3时必须调用call_support_agent。
