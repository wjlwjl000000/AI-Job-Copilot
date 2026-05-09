---
name: build-profile
description: Use when a resume file has been uploaded and needs parsing into a structured job-seeker profile, or when a profile building task is received from the Supervisor.
---

# Build Profile

## Overview
调用 `parse_document()` 解析当前会话已上传的简历文件，获取结构化画像 JSON，经确认后持久化到 PostgreSQL 并向量化到 Chroma。画像以上传简历为唯一数据源，重新上传即覆盖。

## When to Use
- 用户上传简历后要求构建/更新求职画像
- 用户说"生成我的画像"、"更新画像"、"帮我构建画像"
- 用户重新上传简历，需要以最新简历为准覆盖旧画像

## When NOT to Use
- 未上传简历文件 → 先提示用户上传
- 仅需职位搜索 → `match-jobs`
- 仅需匹配度评估 → `score-match`
- 面试准备 → `generate-interview-qs`

## Workflow
以下步骤必须按序逐一执行。每步仅调用一个工具，调用完成后必须立即进入下一步，禁止在任何步骤提前终止（步骤6除外）。

**步骤1** — 调用 read_profile()
- 返回空数组 [] → 属于首次创建画像的正常情况，正常进入步骤2
- 返回已有画像 → 调用 confirm_overwrite(messages="检测到已有画像（姓名：{name}），是否覆盖？")
  - 用户确认 → 进入步骤2
  - 用户拒绝 → 跳到步骤6，以自然语言输出"画像未更改，保留原画像"

**步骤2** — 调用 parse_document()
- 返回 `{data: null, errors: [...]}` → 描述 errors 内容，提示用户上传简历或重试，跳到步骤6
- 返回 `{data: {...}, errors: [...]}` → data 可用但存在校验缺失，记住 errors 内容，继续进入步骤3
- 返回 `{data: {...}, errors: []}` → 正常进入步骤3

**步骤3** — 调用 chroma_insert(collection="profiles", documents=[summary], metadatas=[{"profile_id": "步骤2返回 data 中的 id"}])
- summary 模板(必须遵守)：`"{姓名}，{work_years}年经验，技能：{skills}，目标岗位：{roles}"`
- 示例：`"巫佳龙，0年经验，技能：Python、FastAPI、Docker，目标岗位：AI应用开发"`
- chroma_insert 返回后必须立即进入步骤4

**步骤4** — 调用 db_write(table="user_profiles", data=步骤2返回的 data)
- 步骤1 无画像 → 直接传入 data
- 步骤1 有画像 → 额外传入 record_id=已有画像ID
- db_write 返回后必须立即进入步骤5

**步骤5** — 调用 save_resume(messages="是否保存当前解析的简历文件-{步骤2返回 data 中的 id}\n注意：不保存则可能影响后续简历优化环节")
- 触发系统中断，前端弹窗询问用户是否保存原始简历
- save_resume 返回后必须立即进入步骤6

**步骤6** — 以自然语言输出全面、具体的总结，描述构建的画像内容：姓名、联系方式、教育背景、技能列表（含等级）、项目经历、工作年限、求职目标等。步骤2中如有 errors 在此时提及（如"部分字段未能解析：..."）。

## Common Mistakes
- 已有画像时不询问直接覆盖 → 必须返回 input-required 等待用户确认
- chroma_insert 的 documents 只传姓名 → 必须按模板拼接完整 summary
- 画像数据直接来自 parse_document 返回值，不编造、不二次加工

## Examples

### 示例1：首次构建
步骤1: read_profile() → []
步骤2: parse_document() → {data: {id:"xxx", name:"张三", ...}, errors: []}
步骤3: chroma_insert(collection="profiles", documents=["张三，4年经验，技能：..."], metadatas=[{...}])
步骤4: db_write(table="user_profiles", data={...})
步骤5: save_resume(messages="是否保存...-xxx") → 中断确认
步骤6: 自然语言总结："已为您构建求职画像。姓名张三，4年工作经验，技能包括Python（高级）、FastAPI（中级）...教育背景为XX大学计算机科学本科。求职目标为北京地区的AI工程师岗位..."

### 示例2：已有画像覆盖
步骤1: read_profile() → [{id:"prof-abc123", name:"张三"}]
       → confirm_overwrite(messages="检测到已有画像（姓名：张三），是否覆盖？") → 用户确认
步骤2: parse_document() → {data: {...}, errors: []}
步骤3: chroma_insert(...)
步骤4: db_write(table="user_profiles", data={...}, record_id="prof-abc123")
步骤5: save_resume(messages="是否保存...-xxx") → 中断确认
步骤6: 自然语言总结（同上）

### 示例3：解析有校验警告
步骤1: read_profile() → []
步骤2: parse_document() → {data: {id:"xxx", name:"李四", skills:[], ...}, errors: ["缺失: skills"]}
步骤3: chroma_insert(collection="profiles", documents=["李四，2年经验，技能：...，目标岗位：..."], ...)
步骤4: db_write(table="user_profiles", data={...})
步骤5: save_resume(messages="是否保存...-xxx") → 中断确认
步骤6: 自然语言总结："已为您构建求职画像。姓名李四...注意：简历中未解析到技能信息，建议手动补充。"
