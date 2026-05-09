---
name: match-jobs
description: Use when the user wants to discover job openings matching their profile, needs skill-based career recommendations, or after profile updates when new positions should be suggested.
---

# Match Jobs

## Overview
基于用户画像中的技能、目标岗位、城市和薪资偏好，从外部招聘平台搜索当前开放职位，逐条评分排序后返回匹配结果。

## When to Use
- 用户说"帮我搜职位"或"有什么适合我的岗位"
- 画像刚构建完成，需要初始职位推荐
- 用户想按新的方向探索职位机会

## When NOT to Use
- 已有目标 JD 需要详细评分 → `score-match`
- 需要针对 JD 优化简历 → `optimize-resume`
- 未构建求职画像 → `build-profile` 先

## Workflow
以下步骤必须按序逐一执行。每步完成后必须立即进入指定下一步，禁止跳过或提前终止（步骤4除外）。

**步骤1** — 调用 db_read(table="user_profiles", fields=["skills", "target"]) 获取搜索条件
- 返回空数组 → 输出"尚未构建求职画像，请先上传简历"，跳到步骤4
- 返回画像 → 提取以下字段后进入步骤2：
  - skills（技能标签列表）
  - target.roles（目标岗位列表）
  - target.cities（目标城市列表）
  - target.salary_range（期望薪资范围）
- skills 和 target.roles 均为空 → 输出"画像缺少技能和岗位方向，无法搜索"，跳到步骤4

**步骤2** — 调用 web_search(query, source="boss") 搜索职位
- query 拼接规则：取 target.roles[0] + 空格 + skills 前3个 + 空格 + target.cities[0]
  - 示例：target.roles=["AI工程师"], skills=["Python","FastAPI","Docker","React"], cities=["北京"] → query="AI工程师 Python FastAPI Docker 北京"
  - roles 为空时用"开发工程师"替代
  - cities 为空时不添加城市关键词
- 返回空数组 → 输出"未搜索到匹配职位，建议尝试：①扩大城市范围 ②放宽岗位关键词"，跳到步骤4
- 返回结果 → 进入步骤3

**步骤3** — Agent 推理阶段（不调用工具）：逐条评分排序
对步骤2返回的每条职位，必须完成以下分析后才能进入步骤4：

1. 提取 JD 中的技能要求列表 — 从 jd_content 中识别所有技术栈、工具、领域关键词，标注哪些是必须项
2. 计算技能重合度 — 将步骤1的 skills 与提取的技能要求逐项对比，命中数/要求总数
3. 城市匹配 — 步骤1的 cities 包含职位所在城市=加分
4. 薪资匹配 — 步骤1的 salary_range 与职位薪资范围有重叠=加分
5. 综合上述因素给出 0-1 综合匹配分
6. 过滤：score < 0.4 的职位不列入最终结果
7. 按 score 降序排列，取前10条

每条的 reason 字段必须包含：技能重合点 + 主要差距点（一句话概括，不空洞）

**步骤4** — 以自然语言输出搜索结果：
- 共搜索到 N 个职位，筛选后展示 M 个（score >= 0.4）
- 每题包含：公司、岗位、薪资、城市、综合匹配分、推荐理由
- 按 score 降序呈现
- 如最高分 < 0.6：提醒用户"当前画像匹配的岗位较少，建议优化简历或扩大搜索条件"
- 如搜索结果中某个岗位 score >= 0.7：建议"该岗位匹配度较高，可使用 score-match 进行详细评估"
- 如用户画像中无目标 JD，在末尾询问是否需要针对某具体岗位做详细评分

## Common Mistakes
- 只搜不评分 → 步骤3必须逐条评分，web_search 原始结果不直接展示给用户
- skills 全量拼入 query 导致搜索词过长 → 步骤2只取前3个核心技能
- 技能要求提取不全 → 步骤3需从 jd_content 全文提取，不只看标题
- 忽略 city 和 salary 过滤 → 步骤3评分时纳入城市和薪资匹配
- score < 0.4 的岗位也展示 → 步骤3需过滤低分结果

## Examples

### 示例1：标准搜索
步骤1: db_read(table="user_profiles", fields=["skills", "target"]) → {skills:["Python","FastAPI","Docker","PostgreSQL"], target:{roles:["AI应用开发"], cities:["北京"], salary_range:"15-25K"}}
步骤2: web_search(query="AI应用开发 Python FastAPI Docker 北京", source="boss") → 返回23条
步骤3: 逐条评分 → 过滤score<0.4后剩15条 → 取前10按score降序
步骤4: "共搜索到23个职位，筛选后为您推荐15个（综合匹配分>=0.4），以下展示前10个：1. XX科技-AI应用开发工程师-20-30K-北京-score:0.82-技能高度重合..."

### 示例2：搜索无结果
步骤1: db_read(table="user_profiles", fields=["skills", "target"]) → {skills:["冷门技术X"], target:{roles:["极小众岗位"], cities:["拉萨"]}}
步骤2: web_search(query="极小众岗位 冷门技术X 拉萨", source="boss") → []
步骤4: "未搜索到匹配职位。建议尝试：①将城市范围扩大至周边省会 ②放宽岗位方向至技术通用岗位..."

### 示例3：无画像直接搜索
步骤1: db_read(table="user_profiles", fields=["skills", "target"]) → [] → 输出"尚未构建求职画像，请先上传简历"，终止
