---
name: parse-resume
description: 当用户上传或更新简历文件时，需要解析文件并提取结构化信息。适用于PDF、Word、纯文本格式。
---

# 简历解析

## 目标
将上传的简历文件解析为结构化内容，提取关键信息。

## 工作流程
1. 使用 parse_document 工具解析文件 → 获取原始文本和元数据
2. 使用 call_llm 从原始文本中提取：
   - 个人基本信息
   - 教育经历（学校、专业、学历）
   - 工作经历（公司、岗位、年限）
   - 技能标签（技术栈、软技能）
   - 项目经验
3. 如遇到关键信息缺失（如学历），返回 state: "input-required" 请求用户补充

## 输出格式
{"raw_text": str, "structured": {"skills": [...], "education": {...}, "experience": [...], "projects": [...]}}
