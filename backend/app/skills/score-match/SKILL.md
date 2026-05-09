---
name: score-match
description: Use when the user wants to evaluate how well their profile matches a specific JD, or when a resume-JD pair needs multi-dimensional scoring with gap analysis.
---

# Score Match

## Overview
从技能、经验、学历、薪资四个维度逐一评估用户画像与目标 JD 的匹配度，产出加权总分、差距分析和改进建议。低分时自动触发情感支持。

## When to Use
- 用户说"我和这个岗位匹配吗"或"评估一下匹配度"
- `match-jobs` 找到岗位后需对具体 JD 详细评分
- 优化简历前想先了解差距

## When NOT to Use
- 未构建求职画像 → `build-profile` 先
- 用户画像无 target.jd → 先引导用户提供目标 JD
- 仅需搜索职位 → `match-jobs`
- 仅需优化简历 → `optimize-resume`

## Workflow
以下步骤必须按序逐一执行。每步完成后必须立即进入指定下一步，禁止跳过或提前终止（步骤5除外）。

**步骤1** — 调用 db_read(table="user_profiles", fields=["skills", "work_years", "education", "target"]) 获取画像和目标 JD
- 返回空数组 → 输出"尚未构建求职画像，请先上传简历"，跳到步骤5
- 返回画像但 target.jd 为空 → 输出"未指定目标JD，请提供目标岗位描述后再评估"，跳到步骤5
- 返回画像且 target.jd 有内容 → 提取以下数据并进入步骤2：
  - profile.skills（技能列表及等级）
  - profile.work_years（工作年限）
  - profile.education（学历信息）
  - profile.target.salary_range（期望薪资）
  - target.jd.requirements（JD 技能要求列表）
  - target.jd.title（目标岗位名）
  - target.jd.salary_range（JD 薪资范围，如有）

**步骤2** — Agent 推理阶段（不调用工具）：四维度逐一评分
必须按以下顺序完成四个维度的评分，每个维度评完后记录分数和依据，全部完成后才能进入步骤3：

维度一 — 技能重合度 (skill_match, 权重 0.40)：
- 从步骤1的 target.jd 内容中提取所有技能要求（硬性+优先）
- 逐项与 profile.skills 对比，统计 匹配数 / 要求总数
- 标注缺失技能，尤其标记 jd.requirements 中 required=true 的项
- 得出 0-1 分数：全匹配=1.0，缺一项硬性扣 0.2，缺一项优先扣 0.1

维度二 — 经验匹配度 (experience_match, 权重 0.25)：
- 从 jd 内容中推断经验年限要求和行业方向要求
- 对比 profile.work_years：达标得满分，每差1年扣0.15
- 对比行业方向（如profile的行业 vs jd所在行业）是否一致
- 得出 0-1 分数

维度三 — 学历匹配度 (education_match, 权重 0.15)：
- 从 jd 内容中提取学历要求
- 对比 profile.education.degree：达标得满分，差一级扣0.3
- 得出 0-1 分数

维度四 — 薪资匹配度 (salary_match, 权重 0.20)：
- 将 profile.target.salary_range 与 jd 中的薪资范围对比
- 期望薪资完全落在JD范围内=1.0
- 期望薪资部分超出=0.5，完全超出=0.0
- JD未标注薪资范围时默认为0.5（中性）
- 得出 0-1 分数

加权总分：overall = skill_match × 0.40 + experience_match × 0.25 + education_match × 0.15 + salary_match × 0.20

**步骤3** — [条件] overall < 0.6
→ 必须调用 call_support_agent(trigger="low_match", context={overall, key_gaps: 从步骤2提取的前3个缺失项})
→ 返回后进入步骤4
overall >= 0.6 → 直接进入步骤4

**步骤4** — [条件] overall < 0.8 且步骤2中有可通过优化简历改善的差距（如技能关键词缺失、项目描述不匹配）
→ 在步骤5的总结中附带："该岗位匹配度有提升空间，是否需要我针对此JD优化您的简历？"
→ 进入步骤5

**步骤5** — 以自然语言输出完整评分报告：
- 目标岗位：[title]，加权总分：overall
- 四个维度分别得分及分析依据
- 匹配亮点（strengths）：得分较高的维度及具体匹配项
- 差距分析（gaps）：逐项列出缺失技能/条件，标注是否为JD硬性要求
- 改进建议（suggestions）：针对每个差距的可操作建议
- 如步骤4触发，结尾附带优化建议询问

## Common Mistakes
- 评分时只凭印象不逐项对比 → 步骤2必须按四维度逐一分析，每项记录依据
- overall < 0.6 时忘记调用 call_support_agent → 步骤3 是强制条件
- 技能对比只数数量不关注 required 标记 → required=true 的技能缺失需重点标注
- 数据来源错误 → 所有画像数据来自步骤1的 user_profiles，不从其他表获取

## Examples

### 示例1：高分匹配
步骤1: db_read(table="user_profiles", fields=["skills", "work_years", "education", "target"]) → skills:[Python, FastAPI, Docker], work_years:3, target.jd:{title:"Python后端", requirements:[...]}
步骤2: 技能=0.85(缺K8s), 经验=0.9(要求3年/用户3年), 学历=1.0(要求本科/用户本科), 薪资=1.0 → overall=0.91
步骤3: overall>=0.6，跳过
步骤4: overall>=0.8，跳过
步骤5: "针对Python后端岗位，您的综合匹配度为0.91。技能重合度85%（缺失K8s为加分项非硬性要求），经验与学历完全匹配..."

### 示例2：低分触发支持
步骤1: db_read(table="user_profiles", fields=["skills", "work_years", "education", "target"]) → skills:[基础Python], work_years:0, target.jd:{title:"高级AI工程师", requirements:[{skill:"LLM微调", required:true}, ...]}
步骤2: 技能=0.15(缺大量硬性技能), 经验=0.0(要求5年/用户0年), 学历=0.7, 薪资=1.0 → overall=0.26
步骤3: overall<0.6 → call_support_agent(trigger="low_match", context={overall:0.26, key_gaps:["LLM微调","分布式训练","生产部署经验"]})
步骤4: overall<0.8且差距大 → 触发优化建议
步骤5: "该岗位与您当前画像的匹配度为0.26。核心差距在于：①缺少LLM微调经验（硬性要求）②工作年限差距5年..."
