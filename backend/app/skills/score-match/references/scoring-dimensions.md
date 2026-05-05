# Match Scoring Dimensions

## 1. Skill Match (技能重合度)
Weight: 0.40

| Criteria | Weight | Description |
|----------|--------|-------------|
| Required skills covered | 0.5 | JD-required skills present in profile |
| Skill level match | 0.3 | Profile level vs JD required level (中级 vs 要求高级 → penalty) |
| Bonus skills | 0.2 | Profile has skills JD marks as "preferred" |

## 2. Experience Match (经验匹配度)
Weight: 0.35

| Criteria | Weight | Description |
|----------|--------|-------------|
| Years of experience | 0.4 | Profile years vs JD years (within ±2 years → 1.0, ±5 years → 0.5) |
| Role alignment | 0.3 | Previous roles vs JD role category |
| Industry match | 0.2 | Previous industry vs JD industry |
| Project relevance | 0.1 | Project descriptions align with JD responsibilities |

## 3. Education Match (学历匹配度)
Weight: 0.15

| Degree Level | Score |
|-------------|-------|
| Exact match or higher | 1.0 |
| One level below | 0.6 |
| Two+ levels below | 0.3 |
| Major/field match | +0.2 bonus |

## 4. Salary Match (薪资匹配度)
Weight: 0.10

| Situation | Score |
|-----------|-------|
| Expectation within JD range | 1.0 |
| Expectation < JD min | 0.7 (undervaluing) |
| Expectation > JD max by < 20% | 0.5 |
| Expectation > JD max by > 20% | 0.2 |

## Overall Score
`overall = 0.40 * skill + 0.35 * experience + 0.15 * education + 0.10 * salary`
