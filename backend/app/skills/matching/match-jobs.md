---
name: match-jobs
description: 当用户希望搜索发现匹配的职位机会、或系统需要自动推荐职位时使用。
---

# 职位匹配搜索

## 目标
基于用户画像搜索匹配的职位。

## 工作流程
1. 使用 db_read 获取画像技能向量
2. 使用 chroma_query 从 jobs collection 语义搜索
3. 使用 call_llm 排序并生成推荐理由

## 输出格式
{"matches": [{"job_id": str, "title": str, "company": str, "score": float, "reason": str}, ...]}
