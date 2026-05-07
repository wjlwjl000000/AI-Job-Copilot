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

## Data Models

### user_profiles（读）
| 字段 | 类型 | 含义 |
|------|------|------|
| skill_tags | JSON | 技能标签 |
| work_years | INT | 工作年限 |
| target | JSON | 求职目标：{roles} |
| 触发事件 | — | 触发信息由调用方通过A2A传入，非db_read直接获取 |

### stories — chroma_query("stories", ...) 返回
| 字段 | 类型 | 含义 |
|------|------|------|
| content | TEXT | 真实求职经历原文（必须原样引用，不可修改或总结） |
| source | STR | 来源："crawled"|"user_contributed"|
| score | FLOAT | 与查询的语义相似度 |

## Examples

### 示例1：匹配度低→检索相似经历并鼓励
**场景**：Matching Agent检测到匹配度0.35，通过A2A触发call_support_agent(trigger="low_match")。

**工具调用序列**：
1. db_read("user_profiles") → [{skill_tags: [{"name": "Python","level": "中级"}], work_years: 2, target: {roles: ["AI工程师"]}}]

2. chroma_query("stories", "2年Python开发 AI工程师 匹配度低 求职挫折") → [{content: "我刚开始找AI方向的工作时，投了50多份简历只有2个面试。后来我花了1个月系统学习了机器学习基础，同时做了一个开源项目来证明动手能力。第3个月终于拿到了心仪的offer。", source: "user_contributed", score: 0.89}]

3. 在Thought中生成鼓励（不调用额外工具，数据来自步骤1和2）：
   - 共情：匹配度低确实令人沮丧
   - 引故事：引用步骤2返回的story.content原文
   - 建设性收尾：可以从补强算法基础+做开源项目入手

**最终输出**：
{
  "story": "我刚开始找AI方向的工作时，投了50多份简历只有2个面试。后来我花了1个月系统学习了机器学习基础，同时做了一个开源项目来证明自己的动手能力。第3个月终于拿到了心仪的offer。",
  "encouragement": "匹配度低确实让人沮丧。之前有位2年Python经验的候选人也经历过类似阶段，投了50份才2个面试。但他花1个月补了算法基础+做了个开源项目，第3个月就拿到了offer。这不是对你能力的否定——可以从补强算法基础入手，需要我帮你规划学习路线吗？",
  "source": "user_contributed"
}

### 示例2：未找到匹配故事→通用模板
**场景**：用户触发场景特殊，Chroma中无相似故事。

**工具调用序列**：
1. db_read("user_profiles") → [{skill_tags: [...], work_years: 5, ...}]
2. chroma_query("stories", "...") → []（无匹配结果）

3. 在Thought中判断：无真实故事，使用通用鼓励模板。story字段留空，source设为"general"，不编造故事。

**最终输出**：
{
  "story": "",
  "encouragement": "求职路上遇到挫折是每个人都会经历的阶段。你目前积累了5年的开发经验，这本身就是很有价值的资本。每一次被拒都是一次调整方向的机会——可以重新审视目标岗位和自己的匹配点，也许下一个机会就是你的转折点。",
  "source": "general"
}

> 示例中的字段值来自db_read和chroma_query返回的实际数据。story必须原样引用chroma_query返回的content，不得修改或总结。无故事时story留空、source="general"，不得编造故事。
