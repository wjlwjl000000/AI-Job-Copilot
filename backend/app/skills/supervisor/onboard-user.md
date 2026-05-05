---
name: onboard-user
description: Use when a new user first uses the system, when the Supervisor needs to determine which agents to dispatch based on user intent, or when the system needs to guide the user through the initial profile setup flow.
---

# 用户引导与意图识别

## 概述
Supervisor 使用此技能识别新用户意图，生成初始引导流程，分解任务并分发给对应 Agent。

## When to Use
- 新用户第一次对话
- Supervisor 收到模糊请求，需拆解意图
- 用户说"帮我找工作""不知道从哪开始"

## When NOT to Use
- 用户意图明确且单一 → 直接 Planner 生成 Plan
- 错误处理 → 这是 Supervisor 的系统性职责

## 工作流程
1. 分析用户最后一条消息 → 识别核心意图（简历/匹配/面试/情感）
2. 基于 Agent Card Registry 的 description 匹配需要的 Agent
3. 生成 Plan（不含 Support）
4. 识别任务依赖（"先A再B" → B depends_on A）

## 意图分类参考
| 用户表述 | 意图 | 对应 Agent |
|---------|------|-----------|
| "上传简历""看看我的简历" | 简历解析 | profile |
| "搜职位""匹配岗位" | 职位匹配 | matching |
| "匹配度""我和这个岗位" | 匹配评估 | matching |
| "优化简历""改简历" | 简历优化 | matching |
| "面试""准备面试" | 面试备战 | interview |
| "被拒了""好难" | 情感支持 | matching/ profile 内部调 support |

## 常见错误
- 自动追加用户未请求的任务 → 软连接原则，不强制流程
- Plan 中包含 Support → Supervisor 不直接调 Support
