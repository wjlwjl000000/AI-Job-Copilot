---
name: build-profile
description: 当简历解析完成、用户补充个人信息后，构建或更新用户求职画像。
---

# 构建求职画像

## 目标
基于简历结构化内容构建用户求职画像。

## 工作流程
1. 使用 db_read 获取现有画像数据
2. 使用 call_llm 从简历内容提取技能标签并分级（初级/中级/高级/专家）
3. 使用 call_llm 计算工作年限
4. 使用 call_llm 生成画像摘要文本（用于向量化）
5. 使用 db_write 将画像数据写入 user_profiles 表
6. 使用 chroma_insert 将画像摘要向量写入 profiles collection
7. 使用 call_llm 对画像进行竞争力评分

## 输出格式
{"profile_id": str, "skill_tags": [...], "work_years": int, "education": {...}, "projects": [...], "scores": {"competitiveness": float, "market_match": float, "completeness": float}}
