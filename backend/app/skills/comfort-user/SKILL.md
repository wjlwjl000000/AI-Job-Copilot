---
name: comfort-user
description: Use when the user experiences rejection, low match scores below 0.6, interview failure, or needs encouragement and shared experiences. Also use during new user onboarding for a welcome message. Only called by other agents via A2A, never dispatched directly by Supervisor.
---

# Comfort User

## Overview
Retrieve similar job-seeking experiences from Chroma based on the user's profile and trigger event, then generate personalized encouragement. Results are always embedded in the caller's response.

## When to Use
- Matching Agent detects match score < 0.6 → encouragement
- Application status set to "rejected" → comfort
- Interview evaluation returned low scores → reflection support
- User received an offer → congratulations
- New user onboarding → welcome message

## When NOT to Use
- No emotion-related trigger active → don't proactively inject
- User explicitly asks not to be comforted
- Technical analysis needed → `score-match` or `evaluate-answer`

## Workflow
1. **先了解用户处境** — db_read("user_profiles") 获取用户的技能标签、经验年限、目标岗位以及当前触发事件（被拒/低匹配/面试失败/入职欢迎）
2. **检索同背景同遭遇的故事** — chroma_query("stories", 用步骤1的关键信息构造查询词：岗位方向 + 工作年限 + 触发事件类型)，找到背景相似且遇到了同样情况的人的真实经历
3. **生成个性化鼓励** — 基于步骤2检索到的真实故事，结合用户的具体处境：
   - 先共情回应：认同用户当下的感受
   - 再引用故事：指出这个人和用户背景相似、经历了同样的遭遇
   - 最后建设性收尾：这件事不能定义用户的价值，给出下一步可尝试的方向

> 步骤3在Agent的Thought阶段自然完成，不需要call_llm工具。语气和结构参考references/messaging-guide.md。

## Output Format
```
{
  "story": "原文片段"（chroma_query 返回的 story.content，不可编造或总结）,
  "encouragement": "≤200字"（共情回应1句+引用故事相似点1句+建设性收尾1句）,
  "source": "crawled | user_contributed"（故事来源标注）
}
```

## Rules
- **Always return `state: "completed"`** — never trigger `input-required`
- Tone must be warm and genuine, not preachy or dismissive
- Results are embedded in caller's return value, never delivered standalone
- If no matching story found in Chroma, use a general encouragement template and set source to "general"

## Common Mistakes
- Fabricating stories not returned by chroma_query → must use verbatim story content
- Generating encouragement without referencing the retrieved story → encouragement must bridge to the specific story
- Returning input-required → Support Agent only returns completed
