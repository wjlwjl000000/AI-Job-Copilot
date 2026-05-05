---
name: onboard-user
description: Use when a new user interacts with the system for the first time, or when the Supervisor needs to decompose a vague request into specific agent tasks based on intent analysis.
---

# Onboard User

## Overview
Supervisor uses this to analyze user intent, map it to available agents from the Card Registry, and generate the initial execution plan. Follows the soft-connection principle: never auto-append tasks the user didn't request.

## When to Use
- First conversation with a new user
- Supervisor receives a vague request ("帮我找工作")
- Need to decompose intent into agent tasks

## When NOT to Use
- User intent is already specific and single → Planner generates Plan directly
- Error handling → system-level concern

## Workflow
1. Analyze user's last message → core intent (resume / matching / interview / support)
2. Match intent to available agents via Agent Card Registry descriptions
3. Generate Plan (without support agent)
4. Identify task dependencies ("先A再B" → B.depends_on = [A])

## Intent Mapping
| User Says | Intent | Agent |
|-----------|--------|-------|
| "上传简历" "看看我的简历" | 简历解析 | profile |
| "搜职位" "匹配岗位" | 职位匹配 | matching |
| "匹配度" "这个岗位适合我吗" | 匹配评估 | matching |
| "优化简历" "改简历" | 简历优化 | matching |
| "准备面试" "面试会问什么" | 面试备战 | interview |
| "被拒了" "好难" | 情感支持 | matching/profile internally calls support |

## Common Mistakes
- Auto-adding tasks user didn't request → soft connection: don't force pipeline
- Including support agent in Plan → Supervisor never dispatches support directly
