# Scoring Formula — Score Match

## 加权总分公式

```
overall = skill_match × 0.40 + experience_match × 0.25 + education_match × 0.15 + salary_match × 0.20
```

---

## 维度一：技能重合度 (skill_match, 权重 0.40)

### 计算逻辑
1. 从 `jd_requirements` 提取所有技能名称 → `jd_skills`
2. 从 `profile_skills` 提取所有技能名称 → `profile_skills`
3. 逐项检查 jd_skills 中的每个技能是否出现在 profile_skills 中
4. 设 J = jd_skills 总数，M = 匹配数

### 评分公式
```
skill_match = M / J
```
如果 J = 0（JD 无技能要求）→ skill_match = 0.5（中性）

### 注意事项
- 忽略大小写对比
- jd_requirements 中 required=true 的技能在输出 `details.missing_required` 中单独列出
- 技能名称匹配采用精确字符串匹配

---

## 维度二：经验匹配度 (experience_match, 权重 0.25)

### 计算逻辑
1. 从 `jd_content` 文本中提取年限要求（如"3年以上"、"5年经验"）
2. 取第一个匹配到的数字作为 `jd_years`；无匹配则 jd_years = 0
3. 用户工作年限 = `profile_work_years`

### 评分公式
```
if jd_years == 0:
    experience_match = 0.7  # JD 未要求经验，中性偏高
elif profile_work_years >= jd_years:
    experience_match = 1.0
else:
    gap = jd_years - profile_work_years
    experience_match = max(0.0, 1.0 - gap × 0.15)
```

---

## 维度三：学历匹配度 (education_match, 权重 0.15)

### 学历等第表
| 学历 | 等级值 |
|------|--------|
| 高中 | 1 |
| 大专 | 2 |
| 本科 | 3 |
| 学士 | 3 |
| 硕士 | 4 |
| 博士 | 5 |
| MBA | 4 |

### 计算逻辑
1. 从 `jd_content` 中提取学历要求关键词 → 查表得 jd_level
2. 从 `profile_education` 数组中取最高学位 → 查表得 profile_level
3. 无匹配关键词 → jd_level = 0

### 评分公式
```
if jd_level == 0:
    education_match = 0.7  # JD 未要求学历，中性偏高
elif profile_level >= jd_level:
    education_match = 1.0
else:
    diff = jd_level - profile_level
    education_match = max(0.0, 1.0 - diff × 0.3)
```

---

## 维度四：薪资匹配度 (salary_match, 权重 0.20)

### 薪资解析规则
从字符串（如 "15-25K"）中提取下限和上限：
- 正则提取所有数字
- 如果 K/k 结尾 → 数值 × 1000
- 取第一个数字为 lower，最后一个数字为 upper（如只有一个数字则 upper = lower + 5000）

### 评分公式
```
if jd_lower == 0 and jd_upper == 0:
    salary_match = 0.5  # JD 未标注薪资，中性
elif profile_lower == 0 and profile_upper == 0:
    salary_match = 0.5  # 用户未标注期望薪资，中性
elif profile_upper < jd_lower:
    salary_match = 0.0  # 期望完全低于 JD 范围
elif profile_lower > jd_upper:
    salary_match = 0.0  # 期望完全高于 JD 范围
elif profile_lower >= jd_lower and profile_upper <= jd_upper:
    salary_match = 1.0  # 期望完全落在 JD 范围内
else:
    # 部分重叠：重叠比例 × 0.5
    overlap = min(profile_upper, jd_upper) - max(profile_lower, jd_lower)
    profile_range = profile_upper - profile_lower or 1
    salary_match = (overlap / profile_range) * 0.5
```
