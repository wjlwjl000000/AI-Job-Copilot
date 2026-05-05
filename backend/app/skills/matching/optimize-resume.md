---
name: optimize-resume
description: 当需要针对特定JD优化简历措辞、匹配度低于0.6、或用户主动请求优化时使用。
---

# 简历优化

## 目标
针对目标JD生成优化版简历，创建新版本不覆盖原版。

## 工作流程
1. 使用 db_read 获取基础简历和JD
2. 使用 call_llm 基于差距分析生成优化版本
3. 使用 db_write 创建新简历版本
4. 标注优化改动点和原因

## 输出格式
{"optimized_resume_id": str, "changes": [{"original": str, "optimized": str, "reason": str}, ...], "improvements": [...]}
