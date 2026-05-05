---
name: build-profile
description: Use when parsed resume data is available and needs to be turned into a structured user profile with skill taxonomy, experience vector, and competitiveness scores, or when the user explicitly asks to refresh their profile data.
---

# 构建求职画像

## 概述
基于简历结构化数据构建用户求职画像，生成技能图谱、竞争力评分，并向量化写入 Chroma。

## When to Use
- `parse-resume` 完成，返回了结构化数据
- 用户说"更新我的资料""生成画像"
- 画像数据过时需要重新评分

## When NOT to Use
- 尚未解析简历 → `parse-resume`
- 只需搜索职位 → `match-jobs`

## 工作流程
1. **db_read**("user_profiles") → 获取现有画像
2. **call_llm**(parsed_data) → 技能分级、计算年限、生成摘要
3. **db_write**("user_profiles", data) → 写入 PostgreSQL
4. **chroma_insert**("profiles", [summary]) → 向量化，供 Support Agent RAG 检索
5. **call_llm**(profile) → 竞争力评分（技术深度、经验广度、市场匹配、完整度）

## 输出格式
```json
{"profile_id": "...", "skill_tags": [{"name": "Python", "level": "高级"}], "work_years": 3, "scores": {"competitiveness": 0.8, "market_match": 0.6, "completeness": 0.9}}
```

## 常见错误
- 忘记 chroma_insert → Support 的 RAG 无法检索用户画像
- 技能未分级 → 全部标"中级"无法区分强弱项
