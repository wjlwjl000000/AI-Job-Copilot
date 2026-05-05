---
name: comfort-user
description: Use when the user experiences rejection, low match scores, interview failure, or needs encouragement, and the agent needs to retrieve similar job-seeking stories via RAG to generate personalized emotional support.
---

# 情感支持

## 概述
通过 Chroma RAG 检索与用户处境相似的求职经历，生成个性化鼓励。结果嵌入调用者返回值，不作为独立消息。

## When to Use
- 匹配度 < 0.6 → 需要鼓励
- 投递被拒 → 需要安慰 + 重新定位
- 面试失败 → 需要复盘鼓励
- 拿到 Offer → 祝贺 + 分享类似成功经历
- 新用户首次使用 → 欢迎鼓励

## When NOT to Use
- 用户未触发情感相关事件 → 不主动打扰
- 需要技术分析 → `score-match` 或 `evaluate-answer`

## 工作流程
1. **chroma_query**("stories", profile_summary + trigger_event) → 检索相似经历
2. **db_read**("user_profiles") → 获取用户画像摘要
3. **call_llm**(stories + profile + trigger) → 生成鼓励：
   - 先共情（"被拒确实不好受"）
   - 再分享相似经历
   - 最后给正向建议（不超过 200 字）

## 输出格式
```json
{"story": "...", "encouragement": "...", "source": "crawled"}
```

## 规则
- 永远返回 `state: "completed"`，不生成 `input-required`
- 语气温和真诚，不鸡汤不空洞
- 结果由调用者嵌入其返回值，不独立推送

## 常见错误
- 鼓励内容泛泛而谈 → 必须基于 chroma_query 的具体故事
- 触发 input-required → Support 永远只返回 completed
