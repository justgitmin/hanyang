from config import KEYWORDS, EXCLUDE_KEYWORDS


def matches_keywords(job: dict) -> bool:
    """제목 + 회사명 기준으로 키워드 필터링"""
    text = f"{job.get('title', '')} {job.get('company', '')} {job.get('tags', '')}".lower()

    # 제외 키워드 체크
    for kw in EXCLUDE_KEYWORDS:
        if kw.lower() in text:
            return False

    # 포함 키워드 체크 (하나라도 매칭되면 통과)
    for kw in KEYWORDS:
        if kw.lower() in text:
            return True

    return False


def apply_filter(jobs: list[dict]) -> list[dict]:
    return [j for j in jobs if matches_keywords(j)]
