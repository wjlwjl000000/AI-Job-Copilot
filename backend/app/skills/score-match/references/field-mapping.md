# Field Mapping — Score Match

JD 数据来源的 profile 和 JD 之间的字段对照关系。评分工具 `calculate_match_score` 的参数名称基于此映射。

## Profile 字段路径 → 参数名

| 参数名 | 字段路径 | 类型 | 说明 |
|--------|---------|------|------|
| profile_skills | `skills[]` | list[{name, level, evidence}] | 技能列表 |
| profile_work_years | `work_years` | int | 工作年限 |
| profile_education | `education[]` | list[{degree, school, major, period}] | 教育经历 |
| profile_salary | `target.salary_range` | str | 期望薪资范围，如 "15-25K" |

## JD 字段路径 → 参数名

| 参数名 | 字段路径 | 类型 | 说明 |
|--------|---------|------|------|
| jd_requirements | `requirements[]` | list[{skill, level, required}] | JD 技能要求 |
| jd_salary | `salary_range` | str | JD 薪资范围，如 "18-30K" |
| jd_content | `jd_content` | str | JD 全文，用于提取年限和学历要求 |

## 技能名称对比

- **profile 技能名取自**：`skills[].name`
- **JD 技能名取自**：`requirements[].skill`
- 对比时忽略大小写，精确匹配
