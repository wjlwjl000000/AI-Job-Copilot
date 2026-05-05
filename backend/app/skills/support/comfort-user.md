---
name: comfort-user
description: 当用户遭遇被拒、匹配度低、面试失败或需要鼓励和经历分享时，匹配相似经历并生成个性化鼓励。
---

# 情感支持

## 目标
在用户遭遇挫折时，通过RAG检索相似求职经历，生成个性化鼓励。

## 工作流程
1. 使用 chroma_query 从 stories collection 检索与用户画像相似的经历
2. 使用 db_read 获取用户画像摘要
3. 使用 call_llm 基于检索结果 + 用户处境 + 触发事件生成鼓励文案
4. 回复语气温和、真诚，不超过200字

## 输出格式
{"story": str, "encouragement": str, "source": str}

## 规则
- 永远返回 state: "completed"，不会请求用户输入
- 结果总是嵌入调用者的返回值
