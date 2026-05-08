---
name: build-profile
description: Use when parsed resume text or skill descriptions are available and need conversion into a structured job-seeker profile for downstream matching, scoring, or interview preparation agents. Also use when an existing profile needs updating with new skills, target roles, or preferences.
---

# Build Profile

## Overview
调用 `parse_document()` 解析当前会话已上传的简历文件，获取结构化画像 JSON，经确认后持久化到 PostgreSQL 并向量化到 Chroma。画像以上传简历为唯一数据源，重新上传即覆盖。

## When to Use
- 用户上传简历后要求构建/更新求职画像
- 用户说"生成我的画像"、"更新画像"、"帮我构建画像"
- 用户重新上传简历，需要以最新简历为准覆盖旧画像

## When NOT to Use
- 未上传简历文件 → 提示用户先上传
- 仅需职位搜索 → `match-jobs`
- 仅需匹配度评估 → `score-match`
- 面试准备 → `generate-interview-qs`

## Workflow(每一步必须严格执行，每一份数据必须严格构建)
以下步骤必须按序逐一执行。每步仅调用一个工具，调用完成后必须立即进入下一步，
禁止在任何步骤输出 Final Answer 或提前终止（步骤6除外）。

**步骤1** — 调用 read_profile()
- 返回空数组 [] → 进入步骤2，不要在此输出任何文字
- 返回已有画像 → 调用 confirm_overwrite(messages="检测到已有画像（姓名：{name}），是否覆盖？")
  - 用户确认 → 进入步骤2
  - 用户拒绝 → 跳到步骤6，输出必须以 "Final Answer:" 开头，说明保留原画像

**步骤2** — 调用 parse_document()
- 返回 error → 调用 react() 继续推理，提示用户上传简历
- 返回 data 含校验警告 → 调用 react() 继续推理，列出缺失字段
- 返回 data 无警告 → 进入步骤3

**步骤3** — 调用 chroma_insert(collection="profiles", documents=[summary], metadatas=[{"profile_id": "步骤2返回的 id"}])
- summary 模板(必须遵守)：`"{姓名}，{work_years}年经验，技能：{skills}，目标岗位：{roles}"`
- 示例：`"巫佳龙，0年经验，技能：Python、FastAPI、Docker，目标岗位：AI应用开发"`
- chroma_insert 返回后必须立即进入步骤4，禁止在此输出 Final Answer

**步骤4** — 调用 save_profile()
- 步骤1 无画像 → save_profile(data=步骤2返回的 data)
- 步骤1 有画像 → save_profile(data=步骤2返回的 data, record_id=已有画像ID)
- save_profile 返回后必须立即进入步骤5，禁止在此输出 Final Answer

**步骤5** — 调用 save_resume(messages="是否保存当前解析的简历文件-{步骤2返回 data 中的 id}")
- 此调用触发系统中断，前端弹窗询问用户是否保存原始简历
- save_resume 返回后必须立即进入步骤6

**步骤6** — 输出必须以 "Final Answer:" 开头，之后严格按 Output Format 格式输出画像数据

## Output Format
```
{
  "name": "姓名",
  "contact": {"phone": "手机号码", "email": "电子邮箱"},
  "basic": {"age": 年龄(int), "gender": "性别", "ethnicity": "民族", "hometown": "籍贯", "political": "政治面貌"},
  "education": [{"degree": "学历", "school": "学校", "major": "专业", "period": "就读时间段"}],
  "skills": [{"name": "技能名", "level": "初级|中级|高级|专家", "evidence": "技能证明或项目描述"}],
  "projects": [{"name": "项目名", "role": "担任角色", "description": "项目简介", "content": "具体内容", "tech_stack": ["技术栈"], "achievements": "成果指标"}],
  "organization": [{"name": "组织名", "duties": "职责描述", "achievements": "成果指标"}],
  "work_years": "工作年限（整数）",
  "target": {"cities": ["期望城市"], "salary_range": "期望薪资范围", "industry": "目标行业", "roles": ["目标岗位"]},
  "scores": {"competitiveness": "0-1竞争力分", "market_match": "0-1市场匹配分", "completeness": "0-1画像完整度分"},
  "summary": "个人简介/自述"
}
```

## Common Mistakes
- 已有画像时不询问直接覆盖 → 必须返回 input-required 等待用户确认
- Skipping chroma_insert → downstream matching/support agents break
- parse_document 返回 error 后继续执行 → 必须终止并提示用户上传简历
- chroma_insert 的 documents 只传姓名 → 必须按模板拼接完整 summary
- 画像 JSON 来自 parse_document 返回值，不要二次调用 call_llm

## Examples

### 示例1：首次构建
步骤1: read_profile() → []
步骤2: parse_document() → {data: {id:"xxx", ...}}
步骤3: chroma_insert(collection="profiles", documents=["张三，4年经验，技能：..."], metadatas=[{...}])
步骤4: save_profile(data={...})
步骤5: save_resume(messages="是否保存...-xxx") → 中断确认
步骤6: Final Answer: {画像JSON}

### 示例2：已有画像覆盖
步骤1: read_profile() → [{id:"prof-abc123", name:"张三"}]
       → confirm_overwrite(messages="检测到已有画像（姓名：张三），是否覆盖？") → 用户确认
步骤2: parse_document() → {data: {...}}
步骤3: chroma_insert(...)
步骤4: save_profile(data={...}, record_id="prof-abc123")
步骤5: save_resume(messages="是否保存...-xxx") → 中断确认
步骤6: Final Answer: {画像JSON}

> save_profile 不触发中断，save_resume 触发中断。步骤1返回空数组时继续执行，不得提前终止。