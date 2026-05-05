---
name: evaluate-answer
description: Use when the user has provided an answer to a mock interview question and needs evaluation, scoring, and improvement suggestions, or when the system is running a simulated interview session.
---

# 评估面试回答

## 概述
评估用户面试回答的质量，从准确性、完整性、表达清晰度评分，给出改进建议和范例回答。

## When to Use
- 用户刚回答了模拟面试问题
- 用户说"评估一下我的回答""这个回答怎么样"
- 模拟面试中每道题都需要评估

## When NOT to Use
- 还未生成面试问题 → `generate-interview-qs`
- 用户只是问面试技巧 → call_llm 直接回答

## 工作流程
1. **call_llm**(question + user_answer + expected_points) → 对比评估：
   - 准确性：技术点是否正确
   - 完整性：是否覆盖要点
   - 表达：逻辑是否清晰
2. 给出 0-10 评分 + 三段式 feedback + improved_answer
3. 评估后如果回答质量较差 → 可调用 **call_support_agent** 鼓励用户

## 输出格式
```json
{"score": 7.5, "feedback": "...", "improved_answer": "...", "suggestions": ["..."]}
```

## 常见错误
- 只打分不给改进方向 → 必须给出具体建议和范例
- 批评语气太重 → 先肯定再改进
