---
name: generate-interview-qs
description: Use when the user has an upcoming interview and needs targeted preparation questions based on the JD and their profile weaknesses, or when the system suggests interview prep after detecting an application in interview stage.
---

# 生成面试问题

## 概述
基于 JD 要求和用户画像弱项，生成 3-5 个针对性面试问题，每题附考点和回答要点。

## When to Use
- 用户说"帮我准备面试""面试会问什么"
- 投递状态进入 "interview" 阶段
- 匹配度评估后发现有明确弱项

## When NOT to Use
- 用户已回答问题需要评估 → `evaluate-answer`
- 仅需面试技巧建议 → call_llm 直接处理

## 工作流程
1. **db_read**("user_profiles") + **db_read**("jobs", id) → 画像 + JD
2. **call_llm**(profile + jd + weaknesses) → 生成 3-5 题：
   - 覆盖画像弱项和 JD 核心要求
   - 每道题含考点（考察什么）、回答要点（应该提到什么）
3. 如需用户补充岗位细节 → 返回 `state: "input-required"`

## 输出格式
```json
{"questions": [{"question": "...", "focus": "考察点", "tips": "回答要点"}, ...]}
```

## 常见错误
- 生成通用问题忽视用户弱项 → 必须基于 profile.weaknesses
- 只出题不给要点 → 每题标注考察点和建议
