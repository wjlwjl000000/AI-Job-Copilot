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
1. **获取原始简历和目标信息** — db_read("user_profiles") 拿技能画像和目标 JD（profile.jd 字段中可能已有用户提供的 JD 内容和 requirements），db_read("resumes") 拿基础版本简历（base_version=true）
2. **生成优化版本** — 基于 references/optimization-guidelines.md 的优化原则：
   - 对照 profile.jd.requirements 调整措辞，使简历关键词更靠近 JD 的技能要求
   - 重新排列技能和经验的优先级，把 JD 要求的放在前面
   - 用具体成果和量化数据替换笼统描述
   - 绝不编造不存在的经验或技能
   - 标注每处改动：原文 → 优化后 → 改动理由

### 无 JD 的通用优化
2. **生成通用优化版** — 基于 references/optimization-guidelines.md：
   - 检查简历完整性：技能描述缺失、缺少量化成果、结构混乱
   - 按通用最佳实践优化措辞、结构和呈现方式
   - 标注每处改动及理由

3. **创建新版本** — db_write("resumes", {user_id, title: "针对XX的优化版"或"通用优化版", base_version: false, target_role, content, match_scores: {}}) 创建新版本

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
- Using db_read("jobs") for JD → JD is stored in user_profiles.jd, not jobs table
