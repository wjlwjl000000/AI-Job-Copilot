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

## Data Models

### user_profiles（读）
| 字段 | 类型 | 含义 |
|------|------|------|
| skill_tags | JSON | 技能标签：[{name, level}] |
| projects | JSON | 项目经验：[{name, description, tech_stack}] |
| jd | JSON | 目标JD：{content, requirements} — 为null时做通用优化 |

### resumes（读/写）
| 字段 | 类型 | 含义 |
|------|------|------|
| id | UUID | 简历版本ID |
| user_id | UUID | 所属用户 |
| title | STR | 版本标题（如"针对XX的优化版"） |
| base_version | BOOL | 是否为基础版本（true=原始，false=优化版） |
| target_role | STR | 目标岗位 |
| content | JSON | 简历内容：{summary, skills, projects, experience, education} |
| file_path | STR | 原始文件路径 |
| match_scores | JSON | 匹配分数记录 |

## Examples

### 示例1：针对JD的定向优化
**场景**：score-match返回overall=0.58，用户说"针对这个JD帮我优化简历"。

**工具调用序列**：
1. db_read("user_profiles") → [{skill_tags: [...], jd: {content: "负责AI应用后端开发，要求：1)精通Python/FastAPI 2)熟悉Docker/K8s 3)有LLM应用开发经验", requirements: [{"skill": "Python","level": "高级","required": true},{"skill": "FastAPI","level": "高级","required": true},{"skill": "Docker","level": "中级","required": true},{"skill": "LLM应用开发","level": "中级","required": true}]}}]

2. db_read("resumes") → [{id: "res-001", base_version: true, content: {summary: "4年Python后端开发经验，熟悉Web框架和数据库...", skills: ["Python", "Django", "MySQL", "Docker"], projects: [{name: "数据报表系统", ...}, {name: "AI客服", ...}]}}]

3. 在Thought中生成优化版（不调用额外工具），对照步骤1的jd.requirements逐条调整：
   - "Django" → "FastAPI"（画像中有该技能，简历未体现——来自步骤1的skill_tags）
   - 新增"Docker容器化部署" → "Docker/Kubernetes容器化部署"（画像中有Docker，来自步骤1）
   - 项目重排：把AI客服项目提前（JD偏好LLM经验）
   - 不加LLM经验（画像中无此技能，不能编造）

4. db_write("resumes", {user_id: "u-default", title: "针对AI应用开发工程师的优化版", base_version: false, target_role: "AI应用开发工程师", content: {...优化后内容...}, match_scores: {}}) → {id: "res-002"}

**最终输出**：
{
  "optimized_resume_id": "res-002",
  "title": "针对AI应用开发工程师的优化版",
  "changes": [
    {"original": "熟悉Web框架和数据库", "optimized": "精通高性能Web框架(FastAPI, Django)，熟悉PostgreSQL/MySQL", "reason": "JD明确要求FastAPI，原简历未体现该技能"},
    {"original": "Docker容器化部署", "optimized": "Docker/Kubernetes容器化部署", "reason": "K8s是JD加分项，画像中有Docker基础"},
    {"original": "项目A(数据报表)在前", "optimized": "项目B(AI客服)提前到第一位", "reason": "JD偏好AI应用开发经验，调整项目优先级"}
  ],
  "improvements": ["关键词对齐JD要求(FastAPI, LLM)", "项目优先级重排", "技能描述精确化"]
}

### 示例2：无JD的通用优化
**场景**：用户说"帮我的简历润色一下"，无特定JD。

**工具调用序列**：
1. db_read("user_profiles") → [{skill_tags: [...], jd: null}]
2. db_read("resumes") → [{id: "res-001", base_version: true, content: {summary: "后开开发，会写接口", skills: ["Python"], projects: [{name: "xx系统", description: "做了后端"}]}}]

3. 在Thought中按通用最佳实践优化（不调用额外工具，仅基于步骤2返回的原文改写）：
   - "后开开发" → "后端开发工程师"（修正错别字）
   - "会写接口" → "独立设计并实现RESTful API接口，日均处理10万+请求"（量化）
   - "做了后端" → "负责后端架构设计与核心模块开发，使用FastAPI+PostgreSQL"（补充技术细节）

4. db_write("resumes", {user_id: "u-default", title: "通用优化版", base_version: false, ...}) → {id: "res-003"}

**最终输出**：
{
  "optimized_resume_id": "res-003",
  "title": "通用优化版",
  "changes": [
    {"original": "后开开发，会写接口", "optimized": "后端开发工程师，独立设计并实现RESTful API接口", "reason": "修正错别字，用专业术语替换口语化表达"},
    {"original": "做了后端", "optimized": "负责后端架构设计与核心模块开发，使用FastAPI+PostgreSQL技术栈", "reason": "补充技术细节，提升可信度"}
  ],
  "improvements": ["修正错别字和口语化表达", "补充量化指标", "添加技术细节"]
}

> 示例中的字段值来自db_read返回的实际数据。优化内容只能改写原文，不得编造用户简历中不存在的经验或技能。如果画像中有技能但简历未体现（如FastAPI），可以从画像中引入。
