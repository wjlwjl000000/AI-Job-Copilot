---
name: parse-resume
description: Use when a user uploads a resume file (PDF, Word, plain text) and needs it parsed into structured fields, or when the agent detects a new file attachment and needs to extract skills, experience, and education from it.
---

# 简历解析

## 概述
将上传的简历文件解析为结构化 JSON，供 `build-profile` 和 `score-match` 消费。

## When to Use
- 用户上传简历文件（PDF / Word / TXT）
- 用户说"看看我的简历""帮忙分析一下简历"
- Agent 检测到新文件需要提取结构信息

## When NOT to Use
- 简历已解析完成，需要更新画像 → `build-profile`
- 需要对简历内容打分 → `score-match`

## 工作流程
1. **parse_document**(file_path) → 获取原始文本
2. **call_llm**(raw_text) → 提取结构化字段：
   - 基本信息、教育经历、工作经历、技能标签、项目经验
3. 信息缺失（如学历不详）→ 返回 `state: "input-required"`

## 输出格式
```json
{"raw_text": "...", "structured": {"skills": [...], "education": {...}, "experience": [...], "projects": [...]}}
```

## 常见错误
- 直接用原始文本当结构化结果 → 必须先 call_llm 提取
- 遇到缺失字段跳过 → 返回 input-required 让用户补充
