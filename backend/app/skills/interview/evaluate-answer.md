---
name: evaluate-answer
description: 当用户完成模拟面试回答，需要评估质量和改进建议时使用。
---

# 评估面试回答

## 目标
评估用户面试回答的质量。

## 工作流程
1. 使用 call_llm 对比用户回答与参考答案
2. 从准确性、完整性、表达清晰度评分
3. 给出改进建议和范例回答

## 输出格式
{"score": float, "feedback": str, "improved_answer": str, "suggestions": [...]}
