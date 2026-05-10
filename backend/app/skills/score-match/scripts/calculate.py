"""Score Match — 确定性四维度评分计算。被 calculate_match_score tool 调用。"""
import re
from typing import Any


EDUCATION_LEVELS = {
    "博士": 5, "博士学位": 5, "博士研究生": 5,
    "硕士": 4, "硕士学位": 4, "硕士研究生": 4, "mba": 4, "emba": 4,
    "本科": 3, "学士": 3, "学士学位": 3, "大学本科": 3, "本科学历": 3,
    "大专": 2, "专科": 2, "大专学历": 2, "专科学历": 2,
    "高中": 1, "中专": 1, "高中学历": 1, "高中及以上": 1,
}


def _parse_salary(s: str) -> tuple[float, float]:
    """从薪资字符串解析 (lower, upper)。例: '15-25K' → (15000, 25000)"""
    nums = re.findall(r"[\d.]+", s or "")
    if not nums:
        return 0.0, 0.0
    lower = float(nums[0])
    upper = float(nums[-1]) if len(nums) > 1 else lower + 5
    if "k" in (s or "").lower() or "K" in (s or ""):
        lower *= 1000
        upper *= 1000
    return lower, upper


def _extract_jd_years(jd_content: str) -> int:
    """从 JD 文本中提取年限要求"""
    patterns = [
        r"(\d+)[\s\-]*年[以之]?[上内]",
        r"(\d+)\s*年.*经验",
        r".*经验.*(\d+)\s*年",
        r"(\d+)\+?\s*年",
    ]
    for p in patterns:
        m = re.search(p, jd_content or "")
        if m:
            return int(m.group(1))
    return 0


def _extract_education_level(jd_content: str) -> int:
    """从 JD 文本中提取学历要求等级"""
    text = (jd_content or "").lower()
    for keyword, level in EDUCATION_LEVELS.items():
        if keyword in text:
            return level
    return 0


def _max_education_level(education: list[dict]) -> int:
    """获取 profile 中最高学历等级"""
    if not education:
        return 0
    max_level = 0
    for edu in education:
        degree = (edu.get("degree") or "").lower()
        for keyword, level in EDUCATION_LEVELS.items():
            if keyword in degree:
                max_level = max(max_level, level)
                break
    return max_level


def calculate(profile_skills: list[dict], profile_work_years: int,
              profile_education: list[dict], profile_salary: str,
              jd_requirements: list[dict], jd_salary: str,
              jd_content: str) -> dict[str, Any]:
    """执行四维度评分，返回结构化结果"""

    # ── 维度一：技能重合度 ──
    profile_skill_names = {s.get("name", "").lower() for s in (profile_skills or [])}
    jd_skill_list = [r.get("skill", "") for r in (jd_requirements or [])]
    required_missing = []
    matched = 0
    for jd_skill in jd_skill_list:
        if jd_skill.lower() in profile_skill_names:
            matched += 1
        else:
            req = next((r for r in (jd_requirements or []) if r.get("skill") == jd_skill), {})
            if req.get("required"):
                required_missing.append(jd_skill)

    jd_count = len(jd_skill_list)
    skill_match = matched / jd_count if jd_count > 0 else 0.5
    skill_matched_names = [s for s in jd_skill_list if s.lower() in profile_skill_names]
    skill_missing_names = [s for s in jd_skill_list if s.lower() not in profile_skill_names]

    # ── 维度二：经验匹配度 ──
    jd_years = _extract_jd_years(jd_content)
    if jd_years == 0:
        experience_match = 0.7
    elif (profile_work_years or 0) >= jd_years:
        experience_match = 1.0
    else:
        gap = jd_years - (profile_work_years or 0)
        experience_match = max(0.0, 1.0 - gap * 0.15)

    # ── 维度三：学历匹配度 ──
    jd_level = _extract_education_level(jd_content)
    profile_level = _max_education_level(profile_education or [])
    if jd_level == 0:
        education_match = 0.7
    elif profile_level >= jd_level:
        education_match = 1.0
    else:
        diff = jd_level - profile_level
        education_match = max(0.0, 1.0 - diff * 0.3)

    # ── 维度四：薪资匹配度 ──
    p_lower, p_upper = _parse_salary(profile_salary or "")
    j_lower, j_upper = _parse_salary(jd_salary or "")
    if j_lower == 0 and j_upper == 0:
        salary_match = 0.5
    elif p_lower == 0 and p_upper == 0:
        salary_match = 0.5
    elif p_upper < j_lower:
        salary_match = 0.0
    elif p_lower > j_upper:
        salary_match = 0.0
    elif p_lower >= j_lower and p_upper <= j_upper:
        salary_match = 1.0
    else:
        overlap = min(p_upper, j_upper) - max(p_lower, j_lower)
        profile_range = p_upper - p_lower or 1
        salary_match = (overlap / profile_range) * 0.5

    # ── 加权总分 ──
    overall = (skill_match * 0.40 + experience_match * 0.25 +
               education_match * 0.15 + salary_match * 0.20)

    return {
        "skill_match": round(skill_match, 2),
        "experience_match": round(experience_match, 2),
        "education_match": round(education_match, 2),
        "salary_match": round(salary_match, 2),
        "overall": round(overall, 2),
        "details": {
            "skill": {
                "jd_count": jd_count,
                "matched": matched,
                "matched_names": skill_matched_names,
                "missing_names": skill_missing_names,
                "required_missing": required_missing,
            },
            "experience": {
                "jd_years": jd_years,
                "profile_years": profile_work_years or 0,
            },
            "education": {
                "jd_level": jd_level,
                "profile_level": profile_level,
            },
            "salary": {
                "profile_lower": p_lower,
                "profile_upper": p_upper,
                "jd_lower": j_lower,
                "jd_upper": j_upper,
            },
        },
    }
