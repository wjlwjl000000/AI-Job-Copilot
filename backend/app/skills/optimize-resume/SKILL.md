---
name: optimize-resume
description: Use when a resume needs tailoring for a specific JD, after score-match shows gaps below 0.6, or when the user requests general resume improvement without a specific JD target.
---

# Optimize Resume

## Overview
Generate an optimized resume version. With a JD target, align keywords and priorities to the requirements. Without a JD, improve based on general best practices (completeness, quantification, structure). Always creates a new version without overwriting the original. Do's and don'ts in `references/optimization-guidelines.md`.

## When to Use
- `score-match` returns overall < 0.6 with a specific JD
- User says "帮我优化简历" or "针对这个岗位改一下"
- User wants general resume improvement without a JD ("我的简历哪里可以更好")

## When NOT to Use
- No resume uploaded → `parse-resume` first
- Need match evaluation before optimizing → `score-match` first
- Base resume not yet built → `build-profile` first

## Workflow

### 有 JD 的定向优化
1. **获取原始简历和目标信息** — db_read(table="user_profiles") 拿技能画像和目标 JD，db_read(table="resumes") 拿基础版本简历（base_version=true）
2. **生成优化版本** — 基于 references/optimization-guidelines.md 的优化原则，对照 jd.requirements 调整措辞，不编造经验，标注每处改动
3. **创建新版本** — db_write(table="resumes", data={user_id, title, base_version: false, target_role, content, match_scores: {}}) 创建新版本，base_version必须为false

> 步骤2在Agent的Thought阶段自然完成，不需要call_llm工具。

## Output Format
```
{
  "optimized_resume_id": "新版本ID",
  "title": "版本标题"（如"针对AI Agent开发的优化版"或"通用优化版"）,
  "changes": [{
    "original": "原文片段",
    "optimized": "优化后片段",
    "reason": "改动理由"（为什么这样改能提升匹配度或简历质量）
  }],
  "improvements": ["改进方向总结"]（结构/关键词/量化/完整性等方面的改进）
}
```

## Common Mistakes
- Overwriting the base version → always create new (base_version=false)
- Fabricating experience to match JD → only rephrase existing content
- Using db_read("jobs") for target info → target info is in user_profiles.target

## Examples

### 示例1：针对JD定向优化
**工具调用**：
1. db_read(table="user_profiles") → {skills, target}
2. db_read(table="resumes") → [{id: "res-001", base_version: true, content: {...}}]
3. Thought：对照jd.requirements改写措辞、重排项目优先级（仅改写原文，不编造）
4. db_write(table="resumes", data={base_version: false, title: "针对XX的优化版", content: {...}})

### 示例2：无JD通用优化
**工具调用**：
1. db_read(table="resumes") → [{id: "res-001", base_version: true, content: {summary: "后开开发，会写接口"}}]
2. Thought：修正错别字、量化成果、补充技术细节
3. db_write(table="resumes", data={base_version: false, title: "通用优化版", content: {...}})

> 所有数据来自db_read返回值。只能改写原文，不得编造经验。base_version必须为false。
