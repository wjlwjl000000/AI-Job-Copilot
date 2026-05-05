---
name: evaluate-answer
description: Use when the user provides an answer to a mock interview question and needs evaluation, scoring on accuracy/completeness/clarity, and actionable improvement suggestions.
---

# Evaluate Answer

## Overview
Evaluate a user's interview answer against expected points, scoring on three dimensions. See `references/evaluation-rubric.md` for detailed scoring criteria.

## When to Use
- User just answered a mock interview question
- User says "评估一下我的回答" or "这个回答怎么样"
- Simulated interview session, each answer needs feedback

## When NOT to Use
- No questions generated yet → `generate-interview-qs`
- General interview advice → call_llm directly

## Workflow
1. **call_llm**(question + user_answer + expected_points) → compare:
   - Accuracy: technical correctness
   - Completeness: key points covered
   - Clarity: logical structure
2. Score 0-10 + three-part feedback + improved example
3. Low score → consider **call_support_agent** for encouragement

## Output Format
```json
{"score": 7.5, "feedback": "...", "improved_answer": "...", "suggestions": ["..."]}
```

## Common Mistakes
- Score only, no improvement direction → must give specific suggestions
- Overly critical tone → acknowledge strengths first
