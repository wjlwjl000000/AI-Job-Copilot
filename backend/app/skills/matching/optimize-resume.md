---
name: optimize-resume
description: Use when a resume needs tailoring for a specific JD, after score-match reveals gaps (below 0.6), or when the user explicitly asks to improve their resume wording for a target role.
---

# 简历优化

## 概述
针对目标 JD 生成优化版简历，创建新版本不覆盖原版，标注每处改动及原因。

## When to Use
- `score-match` 返回 overall < 0.6
- 用户说"帮我优化简历""针对这个岗位改一下"
- 匹配度不满意需要针对性提升

## When NOT to Use
- 尚未做 score-match → 先评分定位差距
- 只需匹配分析 → `score-match`

## 工作流程
1. **db_read**("resumes") → 获取基础版本
2. **db_read**("jobs", id) → 获取 JD 及 gaps
3. **call_llm**(resume + jd + gaps) → 优化版本：
   - 突出 JD 匹配的技能和经验
   - 调整措辞对齐 JD 关键词
   - 保持真实，不编造经历
4. **db_write**("resumes", optimized) → 新版本（base_version=false）

## 输出格式
```json
{"optimized_resume_id": "...", "changes": [{"original": "...", "optimized": "...", "reason": "..."}], "improvements": [...]}
```

## 常见错误
- 覆盖原版 → 必须创建新版本
- 编造不存在的经验 → 只调整措辞和呈现角度
