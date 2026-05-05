---
name: generate-interview-qs
description: 当用户获得面试机会，需要针对性生成面试问题和准备建议时使用。
---

# 生成面试问题

## 目标
基于JD和用户画像弱项生成针对性面试问题。

## 工作流程
1. 使用 db_read 获取JD+画像数据
2. 使用 call_llm 分析弱项并生成3-5个面试问题
3. 每题附上考点说明和回答要点

## 输出格式
{"questions": [{"question": str, "focus": str, "tips": str}, ...]}
