"""Score Match — 确定性四维度评分计算 tool。评分规则见 skills/score-match/references/"""
import re
from typing import Annotated, Any
from langchain_core.tools import tool


EDUCATION_LEVELS = {
    "博士": 5, "博士学位": 5, "博士研究生": 5,
    "硕士": 4, "硕士学位": 4, "硕士研究生": 4, "mba": 4, "emba": 4,
    "本科": 3, "学士": 3, "学士学位": 3, "大学本科": 3, "本科学历": 3,
    "大专": 2, "专科": 2, "大专学历": 2, "专科学历": 2,
    "高中": 1, "中专": 1, "高中学历": 1, "高中及以上": 1,
}


def _parse_salary(s: str) -> tuple[float, float]:
    nums = re.findall(r"[\d.]+", s or "")
    if not nums:
        return 0.0, 0.0
    lower = float(nums[0])
    upper = float(nums[-1]) if len(nums) > 1 else lower + 5
    if "k" in (s or "").lower():
        lower *= 1000
        upper *= 1000
    return lower, upper


def _extract_jd_years(jd_content: str) -> int:
    for p in [r"(\d+)[\s\-]*年[以之]?[上内]", r"(\d+)\s*年.*经验",
              r".*经验.*(\d+)\s*年", r"(\d+)\+?\s*年"]:
        m = re.search(p, jd_content or "")
        if m:
            return int(m.group(1))
    return 0


def _extract_education_level(jd_content: str) -> int:
    text = (jd_content or "").lower()
    for keyword, level in EDUCATION_LEVELS.items():
        if keyword in text:
            return level
    return 0


def _max_education_level(education: list[dict]) -> int:
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


@tool
def calculate_match_score(
    profile_skills: Annotated[list[dict], "用户画像的技能列表，必填。来源: db_read 返回的 skills 字段"],
    profile_work_years: Annotated[int, "用户工作年限，必填。来源: db_read 返回的 work_years 字段"],
    profile_education: Annotated[list[dict], "用户教育经历列表，必填。来源: db_read 返回的 education 字段"],
    profile_salary: Annotated[str, "用户期望薪资范围，必填。来源: db_read 返回的 target.salary_range 字段，如 '15-25K'"],
    jd_requirements: Annotated[list[dict], "JD 技能要求列表，必填。来源: db_read 返回的 requirements 字段或 jd_content 提取"],
    jd_salary: Annotated[str, "JD 薪资范围，必填。来源: db_read 返回的 salary_range 字段，如 '18-30K'"],
    jd_content: Annotated[str, "JD 全文，必填。用于提取经验年限和学历要求"],
) -> dict[str, Any]:
    """四维度匹配度评分计算。返回 {skill_match, experience_match, education_match, salary_match, overall, details}。
    评分规则参见 skills/score-match/references/ 目录。"""
    # ── 维度一：技能重合度 ──
    profile_skill_names = {s.get("name", "").lower() for s in (profile_skills or [])}
    jd_skill_list = [r.get("skill", "") for r in (jd_requirements or [])]
    required_missing, matched = [], 0
    for jd_skill in jd_skill_list:
        if jd_skill.lower() in profile_skill_names:
            matched += 1
        else:
            req = next((r for r in (jd_requirements or []) if r.get("skill") == jd_skill), {})
            if req.get("required"):
                required_missing.append(jd_skill)
    jd_count = len(jd_skill_list)
    skill_match = matched / jd_count if jd_count > 0 else 0.5
    skill_matched = [s for s in jd_skill_list if s.lower() in profile_skill_names]
    skill_missing = [s for s in jd_skill_list if s.lower() not in profile_skill_names]

    # ── 维度二：经验匹配度 ──
    jd_years = _extract_jd_years(jd_content)
    pw = profile_work_years or 0
    if jd_years == 0:
        experience_match = 0.7
    elif pw >= jd_years:
        experience_match = 1.0
    else:
        experience_match = max(0.0, 1.0 - (jd_years - pw) * 0.15)

    # ── 维度三：学历匹配度 ──
    jd_level = _extract_education_level(jd_content)
    profile_level = _max_education_level(profile_education or [])
    if jd_level == 0:
        education_match = 0.7
    elif profile_level >= jd_level:
        education_match = 1.0
    else:
        education_match = max(0.0, 1.0 - (jd_level - profile_level) * 0.3)

    # ── 维度四：薪资匹配度 ──
    p_lower, p_upper = _parse_salary(profile_salary or "")
    j_lower, j_upper = _parse_salary(jd_salary or "")
    if j_lower == 0 and j_upper == 0:
        salary_match = 0.5
    elif p_lower == 0 and p_upper == 0:
        salary_match = 0.5
    elif p_upper < j_lower or p_lower > j_upper:
        salary_match = 0.0
    elif p_lower >= j_lower and p_upper <= j_upper:
        salary_match = 1.0
    else:
        overlap = min(p_upper, j_upper) - max(p_lower, j_lower)
        salary_match = (overlap / (p_upper - p_lower or 1)) * 0.5

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
                "jd_count": jd_count, "matched": matched,
                "matched_names": skill_matched, "missing_names": skill_missing,
                "required_missing": required_missing,
            },
            "experience": {"jd_years": jd_years, "profile_years": pw},
            "education": {"jd_level": jd_level, "profile_level": profile_level},
            "salary": {"profile_lower": p_lower, "profile_upper": p_upper,
                       "jd_lower": j_lower, "jd_upper": j_upper},
        },
    }
