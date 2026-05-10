# Education Level Lookup — Score Match

学历关键词到等级值的映射表。`calculate_match_score` 使用此表进行学历比对。

## 关键词映射

| 关键词（jd_content 中出现） | 对应学历要求 |
|---------------------------|-------------|
| 博士、博士学位、博士研究生 | 博士 (5) |
| 硕士、硕士学位、硕士研究生、MBA、EMBA | 硕士 (4) |
| 本科、学士、学士学位、大学本科、本科学历 | 本科 (3) |
| 大专、专科、大专学历、专科学历 | 大专 (2) |
| 高中、中专、高中学历、高中及以上 | 高中 (1) |
| 学历不限、无学历要求 | 不限 (0) |

## profile_education 提取规则

1. 遍历 `profile_education` 数组，取 `degree` 字段的最高值
2. 如果 profile_education 为空数组 → profile_level = 0，education_match = 0.5（中性）
3. 详细评分公式见 `scoring-formula.md` 维度三
