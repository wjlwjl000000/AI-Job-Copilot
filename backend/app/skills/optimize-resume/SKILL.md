---
name: optimize-resume
description: Use when a resume needs tailoring for a specific JD, when score-match returns overall below 0.6, or when the user requests general resume improvement.
---

# Optimize Resume

## Overview
对照目标 JD 或通用优化原则，生成优化后的简历新版本。只改写措辞不编造经历，始终创建新版本（base_version=false）保留原始简历。

## When to Use
- `score-match` 返回 overall < 0.6，需针对 JD 定向优化
- 用户说"帮我优化简历"或"针对这个岗位改一下"
- 用户要求通用简历提升（"我的简历哪里可以更好"）

## When NOT to Use
- 未构建求职画像 → `build-profile` 先
- 未上传简历 → 先引导用户上传后执行 `build-profile`
- 仅需匹配度评估 → `score-match`
- 仅需搜索职位 → `match-jobs`

## Workflow
以下步骤必须按序逐一执行。每步完成后必须立即进入指定下一步，禁止跳过或提前终止（步骤5除外）。

**步骤1** — 调用 db_read(table="user_profiles", fields=["skills", "target"]) 获取画像和目标 JD
- 返回空数组 → 输出"尚未构建求职画像，请先上传简历"，跳到步骤5
- 返回画像数据 → 提取 skills 和 target.jd：
  - target.jd 有内容 → 标记为"定向优化"，进入步骤2
  - target.jd 为空 → 标记为"通用优化"，进入步骤2

**步骤2** — 调用 db_read(table="resumes", filters={user_id, base_version: true}, fields=["id", "content"]) 获取基础版本简历
- 返回空 → 输出"未找到基础版本简历，请先上传并构建画像"，跳到步骤5
- 返回简历 → 提取 content 全文，进入步骤3

**步骤3** — Agent 推理阶段（不调用工具）：逐项优化简历内容
必须完成以下全部操作，并将结果组织好之后才能进入步骤4：

定向优化路径（步骤1标记为"定向"时）：
- 从步骤1的 target.jd.requirements 提取所有技能关键词和软性要求
- 逐段改写简历 content：将用户真实经历用 JD 关键词重新表述，调整项目优先级使匹配项前置
- 每处改动记录三要素：(原文片段, 优化后片段, 改动理由)
- **硬约束**：只能改写措辞和排序，不得添加用户未提及的技能、经验、成果

通用优化路径（步骤1标记为"通用"时）：
- 修正错别字和语法问题
- 将模糊表述转为量化表述（如"负责开发"→"主导开发了X模块，日活Y万"）
- 补充缺失的结构板块（如缺少项目经历、自我评价等提示用户）
- 每处改动记录三要素（同上）

**步骤4** — 调用 db_write(table="resumes", data=构建的数据对象)
data 必须包含以下字段：
- user_id：步骤1返回的 user_id
- title：定向时为"针对{target.jd中的岗位名}的优化版"，通用时为"通用优化版"
- base_version：必须为 false
- target_role：定向时填入岗位名，通用时为空字符串
- content：步骤3生成的完整优化后简历全文
- match_scores：定向时可为空对象{}，通用时为空对象{}
- 返回成功 → 进入步骤5

**步骤5** — 以自然语言输出总结：
- 版本标题
- 改动总数和主要改进方向（关键词对齐/结构优化/量化补充等）
- 选取 2-3 处核心改动举例（原文 → 优化后 → 理由）
- 定向优化时说明改动如何提升与目标 JD 的匹配度
- 通用优化时说明整体简历质量提升点

## Common Mistakes
- 覆盖原始简历 → 步骤4 base_version 必须为 false，始终创建新版本
- 编造用户经历 → 步骤3 只能改写已有内容的措辞
- 目标 JD 信息从 jobs 表查 → JD 在 user_profiles.target.jd 中，用步骤1的数据
- 跳过步骤1 直接优化 → 必须先确认画像和目标 JD 是否存在

## Examples

### 示例1：定向优化
步骤1: db_read(table="user_profiles", fields=["skills", "target"]) → {skills: [...], target: {jd: {requirements: [...], title: "AI Agent开发"}}} → 标记"定向优化"
步骤2: db_read(table="resumes", filters={user_id: "u-1", base_version: true}, fields=["id", "content"]) → [{content: {summary: "后开开发，会写接口", ...}}]
步骤3: 对照 jd.requirements 重写 → summary改为"具备后端开发经验，熟练使用Python/FastAPI构建RESTful API，有Agent工具链集成经验"，记录改动
步骤4: db_write(table="resumes", data={user_id: "u-1", title: "针对AI Agent开发的优化版", base_version: false, ...})
步骤5: 总结："已生成针对AI Agent开发的优化版简历，共12处改动。核心改动：①摘要部分补充Agent工具链关键词 ②项目经历前置Agent相关项目..."

### 示例2：通用优化
步骤1: db_read(table="user_profiles", fields=["skills", "target"]) → {skills: [...], target: {jd: null}} → 标记"通用优化"
步骤2: db_read(table="resumes", ...) → [{content: {summary: "会写代码", experience: [...]}}]
步骤3: 修正+量化 → summary改为"3年后端开发经验，主导过日均10万+请求的API网关项目"
步骤4: db_write(table="resumes", data={title: "通用优化版", base_version: false, ...})
步骤5: 总结："已生成通用优化版简历，共8处改动。主要改进：量化项目成果、补充技术栈细节、优化板块结构..."

### 示例3：无画像直接请求优化
步骤1: db_read(table="user_profiles", fields=["skills", "target"]) → [] → 输出"尚未构建求职画像，请先上传简历"，终止
