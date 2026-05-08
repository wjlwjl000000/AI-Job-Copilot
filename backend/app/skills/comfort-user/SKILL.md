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
1. **了解用户处境** — db_read(table="user_profiles") 获取技能标签、经验年限、目标岗位
2. **检索相似故事** — chroma_query(collection="stories", query=岗位方向+工作年限+触发事件类型, k=3)
3. **生成鼓励** — 基于检索结果：先共情→引故事原文→建设性收尾，Thought阶段完成

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

## Examples

### 示例1：有匹配故事
**工具调用**：
1. db_read(table="user_profiles") → {skills: [...], work_years: 2}
2. chroma_query(collection="stories", query="2年Python AI工程师 求职挫折", k=3) → [{content: "原文...", source: "user_contributed"}]
3. Thought：共情→引用story.content原文→建设性收尾

### 示例2：无匹配故事
**工具调用**：
1. db_read(table="user_profiles") → {work_years: 5}
2. chroma_query(collection="stories", query="...", k=3) → []
3. Thought：无故事，使用通用鼓励，story留空，source="general"

> story必须原样引用chroma_query返回值。无故事时story=""、source="general"，不得编造。
