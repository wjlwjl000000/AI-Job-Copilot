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

**步骤1** — 获取画像和 JD（两个数据缺一不可）：

[1a] JD 获取 — 必须只能选择以下一种方式：

  方式A — 任务数据中有 job_id：
    call: db_read(table="jobs", filters={"id": "<job_id>"})
    → 提取 jd_content（全文）、requirements（技能要求数组）、company（公司名）、salary_range
    → 进入步骤2

  方式B — 任务数据中有 jd_content 文本：
    → 直接使用该文本作为 JD。从文本中自行提取技能要求、岗位名、薪资信息
    → 进入步骤2

  方式C — 以上均无：
    → 输出"未提供目标JD。请指定 job_id 或直接输入 JD 描述"，跳到步骤4

[1b] 画像获取：
  call: db_read(table="user_profiles", fields=["skills", "work_years", "education", "target"])
  → 返回空数组 → 输出"尚未构建求职画像，请先上传简历"，跳到步骤5
  → 返回画像 → 提取 skills、work_years、education、target.salary_range → 进入步骤2

**步骤2** — 调用 calculate_match_score 进行四维度评分：

  评分规则详见 references/ 目录文件：
  - 字段映射关系 → load_reference(skill_name="score-match", ref_path="field-mapping.md")
  - 评分公式规则 → load_reference(skill_name="score-match", ref_path="scoring-formula.md")
  - 学历等第映射 → load_reference(skill_name="score-match", ref_path="education-levels.md")
  （以上三文件可并行加载或在首次评分需要时加载，后续评分可复用。）

  call: calculate_match_score(
    profile_skills=<步骤1的 skills>,
    profile_work_years=<步骤1的 work_years>,
    profile_education=<步骤1的 education>,
    profile_salary=<步骤1的 target.salary_range>,
    jd_requirements=<步骤1的 requirements>,
    jd_salary=<步骤1的 salary_range>,
    jd_content=<步骤1的 jd_content>
  )
  → 返回 {skill_match, experience_match, education_match, salary_match, overall, details}

  call: infer(content="[评分结果] skill_match=<值> | experience_match=<值> | education_match=<值> | salary_match=<值> | overall=<值> | 详情见 details")
  → 进入步骤3

**步骤3** — [条件] overall < 0.6
  → 必须调用 call_support_agent(trigger="low_match", profile_id="<步骤1 画像的 id>", context={overall: <分数>, key_gaps: <details.skill.missing_names 的前3个>})
  → 调用失败时（如连接错误），记录 support_content="（支持服务暂不可用）"，继续执行
  → 返回后进入步骤4
  overall >= 0.6 → 直接进入步骤4

**步骤4** — 以自然语言输出完整评分报告：
- 目标岗位：[来自 JD 的岗位名或公司名]，加权总分：overall（保留两位小数）
- 四个维度分别得分及分析依据
- 匹配亮点（strengths）：得分较高的维度及具体匹配项
- 差距分析（gaps）：逐项列出缺失技能/条件，标注是否为JD硬性要求
- 改进建议（suggestions）：针对每个差距的可操作建议
- 如果步骤2的 overall < 0.8，结尾附带："该岗位匹配度有提升空间，是否需要我针对此JD优化您的简历？"

## Common Mistakes
- db_read 遗漏 table 参数 → 第一个参数必须是表名字符串，如 db_read(table="user_profiles", ...)
- filters 的 key 编造列名 → 必须使用目标表的真实列名（如 jobs 表用 id，不是 job_id）
- 评分时只凭印象不逐项对比 → 步骤2必须按四维度逐一分析，每项记录依据
- overall < 0.6 时忘记调用 call_support_agent → 步骤4 是强制条件
- call_support_agent 遗漏 profile_id → 必须传入步骤1画像的 id
- 数据来源错误 → 画像数据来自 user_profiles，JD 来自 jobs 表或 jd_content 文本

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
