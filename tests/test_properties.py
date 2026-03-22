"""
속성 기반 테스트 (Property-Based Tests)
Feature: job-crawler-enhancement
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from hypothesis import given, settings
import hypothesis.strategies as st

from crawler import crawl_jobkorea, crawl_linkedin, crawl_rocketpunch, crawl_all


# ── 헬퍼: 모의 응답 생성 ──────────────────────────────────────────────────────

def _make_jobkorea_html(jobs):
    """잡코리아 HTML 픽스처 생성"""
    items = ""
    for j in jobs:
        href = j.get("href", "/Recruit/GNo=12345")
        title = j.get("title", "개발자")
        company = j.get("company", "테스트회사")
        tags = j.get("tags", [])
        chip_html = "".join(f'<span class="chip">{t}</span>' for t in tags)
        items += f"""
        <div class="post-list-info">
          <div class="title"><a href="{href}">{title}</a></div>
          <div class="name"><a>{company}</a></div>
          <div class="chip-information-group">{chip_html}</div>
        </div>
        """
    return f'<div class="list-post">{items}</div>'


def _make_linkedin_html(jobs):
    """링크드인 HTML 픽스처 생성"""
    items = ""
    for j in jobs:
        uid = j.get("uid", "9999999")
        title = j.get("title", "Engineer")
        company = j.get("company", "TestCorp")
        items += f"""
        <li data-entity-urn="urn:li:jobPosting:{uid}">
          <h3 class="base-search-card__title">{title}</h3>
          <h4 class="base-search-card__subtitle">{company}</h4>
          <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/{uid}/">view</a>
        </li>
        """
    return f'<ul class="jobs-search__results-list">{items}</ul>'


def _make_rocketpunch_json(jobs):
    """로켓펀치 JSON 픽스처 생성"""
    results = []
    for j in jobs:
        results.append({
            "id": j.get("id", 1),
            "position": j.get("position", "개발자"),
            "company": {"name": j.get("company", "스타트업")},
            "skills": j.get("skills", []),
        })
    return {"data": {"results": results}}


# ── 전략(Strategy) 정의 ───────────────────────────────────────────────────────

safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="<>&\"'"),
    min_size=1,
    max_size=30,
)

job_spec = st.fixed_dictionaries({
    "href": st.just("/Recruit/GNo=99999"),
    "title": safe_text,
    "company": safe_text,
    "tags": st.lists(safe_text, max_size=3),
})

linkedin_job_spec = st.fixed_dictionaries({
    "uid": st.integers(min_value=1, max_value=9999999).map(str),
    "title": safe_text,
    "company": safe_text,
})

rocketpunch_job_spec = st.fixed_dictionaries({
    "id": st.integers(min_value=1, max_value=9999999),
    "position": safe_text,
    "company": safe_text,
    "skills": st.lists(safe_text, max_size=3),
})


# ── Property 1: Job 스키마 완전성 ─────────────────────────────────────────────
# Feature: job-crawler-enhancement, Property 1: Job 스키마 완전성
@given(st.lists(job_spec, min_size=1, max_size=5))
@settings(max_examples=100)
def test_job_schema_completeness_jobkorea(jobs):
    """Validates: Requirements 1.2, 2.2, 3.2, 5.1, 5.2, 5.3"""
    html = _make_jobkorea_html(jobs)
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_jobkorea("테스트")

    required = {"id", "title", "company", "url", "tags", "source"}
    for job in result:
        assert required.issubset(job.keys()), f"필드 누락: {required - job.keys()}"


# Feature: job-crawler-enhancement, Property 1: Job 스키마 완전성
@given(st.lists(linkedin_job_spec, min_size=1, max_size=5))
@settings(max_examples=100)
def test_job_schema_completeness_linkedin(jobs):
    """Validates: Requirements 1.2, 2.2, 3.2, 5.1, 5.2, 5.3"""
    html = _make_linkedin_html(jobs)
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.url = "https://www.linkedin.com/jobs/search/"
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_linkedin("engineer")

    required = {"id", "title", "company", "url", "tags", "source"}
    for job in result:
        assert required.issubset(job.keys()), f"필드 누락: {required - job.keys()}"


# Feature: job-crawler-enhancement, Property 1: Job 스키마 완전성
@given(st.lists(rocketpunch_job_spec, min_size=1, max_size=5))
@settings(max_examples=100)
def test_job_schema_completeness_rocketpunch(jobs):
    """Validates: Requirements 1.2, 2.2, 3.2, 5.1, 5.2, 5.3"""
    data = _make_rocketpunch_json(jobs)
    mock_resp = MagicMock()
    mock_resp.json.return_value = data
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_rocketpunch("개발자")

    required = {"id", "title", "company", "url", "tags", "source"}
    for job in result:
        assert required.issubset(job.keys()), f"필드 누락: {required - job.keys()}"


# ── Property 2: id 접두사 일관성 ──────────────────────────────────────────────
# Feature: job-crawler-enhancement, Property 2: id 접두사 일관성
@given(st.lists(job_spec, min_size=1, max_size=5))
@settings(max_examples=100)
def test_id_prefix_consistency_jobkorea(jobs):
    """Validates: Requirements 1.3, 2.3, 3.3"""
    html = _make_jobkorea_html(jobs)
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_jobkorea("테스트")

    for job in result:
        assert job["id"].startswith("jobkorea_"), f"잘못된 id 접두사: {job['id']}"


# Feature: job-crawler-enhancement, Property 2: id 접두사 일관성
@given(st.lists(linkedin_job_spec, min_size=1, max_size=5))
@settings(max_examples=100)
def test_id_prefix_consistency_linkedin(jobs):
    """Validates: Requirements 1.3, 2.3, 3.3"""
    html = _make_linkedin_html(jobs)
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.url = "https://www.linkedin.com/jobs/search/"
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_linkedin("engineer")

    for job in result:
        assert job["id"].startswith("linkedin_"), f"잘못된 id 접두사: {job['id']}"


# Feature: job-crawler-enhancement, Property 2: id 접두사 일관성
@given(st.lists(rocketpunch_job_spec, min_size=1, max_size=5))
@settings(max_examples=100)
def test_id_prefix_consistency_rocketpunch(jobs):
    """Validates: Requirements 1.3, 2.3, 3.3"""
    data = _make_rocketpunch_json(jobs)
    mock_resp = MagicMock()
    mock_resp.json.return_value = data
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_rocketpunch("개발자")

    for job in result:
        assert job["id"].startswith("rocketpunch_"), f"잘못된 id 접두사: {job['id']}"


# ── Property 3: source 필드 일관성 ────────────────────────────────────────────
# Feature: job-crawler-enhancement, Property 3: source 필드 일관성
@given(st.lists(job_spec, min_size=1, max_size=5))
@settings(max_examples=100)
def test_source_field_consistency_jobkorea(jobs):
    """Validates: Requirements 1.4, 2.4, 3.4"""
    html = _make_jobkorea_html(jobs)
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_jobkorea("테스트")

    for job in result:
        assert job["source"] == "잡코리아", f"잘못된 source: {job['source']}"


# Feature: job-crawler-enhancement, Property 3: source 필드 일관성
@given(st.lists(linkedin_job_spec, min_size=1, max_size=5))
@settings(max_examples=100)
def test_source_field_consistency_linkedin(jobs):
    """Validates: Requirements 1.4, 2.4, 3.4"""
    html = _make_linkedin_html(jobs)
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.url = "https://www.linkedin.com/jobs/search/"
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_linkedin("engineer")

    for job in result:
        assert job["source"] == "링크드인", f"잘못된 source: {job['source']}"


# Feature: job-crawler-enhancement, Property 3: source 필드 일관성
@given(st.lists(rocketpunch_job_spec, min_size=1, max_size=5))
@settings(max_examples=100)
def test_source_field_consistency_rocketpunch(jobs):
    """Validates: Requirements 1.4, 2.4, 3.4"""
    data = _make_rocketpunch_json(jobs)
    mock_resp = MagicMock()
    mock_resp.json.return_value = data
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_rocketpunch("개발자")

    for job in result:
        assert job["source"] == "로켓펀치", f"잘못된 source: {job['source']}"


# ── Property 4: 파싱 실패 시 빈 문자열 폴백 ──────────────────────────────────
# Feature: job-crawler-enhancement, Property 4: 파싱 실패 시 빈 문자열 폴백
@given(st.lists(
    st.fixed_dictionaries({
        "href": st.just("/Recruit/GNo=1"),
        "title": st.just(""),          # 빈 제목
        "company": st.just(""),        # 빈 회사명
        "tags": st.just([]),
    }),
    min_size=1, max_size=5,
))
@settings(max_examples=100)
def test_field_fallback_on_missing_jobkorea(jobs):
    """Validates: Requirements 5.4"""
    html = _make_jobkorea_html(jobs)
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_jobkorea("테스트")

    for job in result:
        for field in ("title", "company", "url", "tags"):
            assert isinstance(job[field], str), f"{field}이 문자열이 아님: {type(job[field])}"
            assert job[field] is not None, f"{field}이 None임"


# Feature: job-crawler-enhancement, Property 4: 파싱 실패 시 빈 문자열 폴백
@given(st.lists(rocketpunch_job_spec, min_size=1, max_size=5))
@settings(max_examples=100)
def test_field_fallback_on_missing_rocketpunch(jobs):
    """Validates: Requirements 5.4"""
    # position, company.name을 None으로 설정하여 폴백 검증
    results = []
    for j in jobs:
        results.append({
            "id": j["id"],
            "position": None,
            "company": {"name": None},
            "skills": None,
        })
    data = {"data": {"results": results}}
    mock_resp = MagicMock()
    mock_resp.json.return_value = data
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_rocketpunch("개발자")

    for job in result:
        for field in ("title", "company", "url", "tags"):
            assert isinstance(job[field], str), f"{field}이 문자열이 아님: {type(job[field])}"
            assert job[field] is not None, f"{field}이 None임"


# ── Property 5: 크롤러 독립 실패 ──────────────────────────────────────────────
# Feature: job-crawler-enhancement, Property 5: 크롤러 독립 실패
@given(
    st.sampled_from(["jobkorea", "linkedin", "rocketpunch"]),
    st.lists(rocketpunch_job_spec, min_size=1, max_size=3),
)
@settings(max_examples=100)
def test_crawler_independent_failure(failing_site, rp_jobs):
    """Validates: Requirements 1.5, 2.5, 3.5, 4.3
    한 크롤러가 예외를 발생시켜도 crawl_all이 나머지 결과를 반환하는지 검증.
    """
    rp_data = _make_rocketpunch_json(rp_jobs)
    jk_html = _make_jobkorea_html([{"href": "/Recruit/GNo=1", "title": "잡코리아공고", "company": "회사A", "tags": []}])
    li_html = _make_linkedin_html([{"uid": "111", "title": "LinkedIn Job", "company": "CorpB"}])

    def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.url = url

        if "jobkorea" in url:
            if failing_site == "jobkorea":
                raise Exception("잡코리아 강제 오류")
            resp.text = jk_html
        elif "linkedin" in url:
            if failing_site == "linkedin":
                raise Exception("링크드인 강제 오류")
            resp.text = li_html
        elif "rocketpunch" in url:
            if failing_site == "rocketpunch":
                raise Exception("로켓펀치 강제 오류")
            resp.json.return_value = rp_data
        return resp

    with patch("requests.get", side_effect=mock_get):
        result = crawl_all(["테스트"], ["jobkorea", "linkedin", "rocketpunch"])

    # 실패한 사이트의 source가 결과에 없어야 함
    site_source_map = {
        "jobkorea": "잡코리아",
        "linkedin": "링크드인",
        "rocketpunch": "로켓펀치",
    }
    failed_source = site_source_map[failing_site]
    sources_in_result = {job["source"] for job in result}
    assert failed_source not in sources_in_result, f"실패한 사이트({failed_source}) 결과가 포함됨"

    # 나머지 사이트 결과는 포함되어야 함
    remaining_sites = [s for s in ["jobkorea", "linkedin", "rocketpunch"] if s != failing_site]
    for site in remaining_sites:
        expected_source = site_source_map[site]
        assert expected_source in sources_in_result, f"정상 사이트({expected_source}) 결과가 누락됨"


# ── Property 6: crawl_all 중복 제거 ──────────────────────────────────────────
# Feature: job-crawler-enhancement, Property 6: crawl_all 중복 제거
@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3),
    st.lists(rocketpunch_job_spec, min_size=1, max_size=5),
)
@settings(max_examples=100)
def test_crawl_all_deduplication(keywords, rp_jobs):
    """Validates: Requirements 4.4"""
    rp_data = _make_rocketpunch_json(rp_jobs)
    mock_resp = MagicMock()
    mock_resp.json.return_value = rp_data
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_resp):
        result = crawl_all(keywords, ["rocketpunch"])

    ids = [job["id"] for job in result]
    assert len(ids) == len(set(ids)), f"중복 id 발견: {[i for i in ids if ids.count(i) > 1]}"


# ── Property 7: SITES 필터링 ──────────────────────────────────────────────────
# Feature: job-crawler-enhancement, Property 7: SITES 필터링
@given(
    st.lists(
        st.sampled_from(["jobkorea", "linkedin", "rocketpunch"]),
        min_size=1, max_size=3,
        unique=True,
    )
)
@settings(max_examples=100)
def test_sites_filtering(selected_sites):
    """Validates: Requirements 4.1, 4.2"""
    jk_html = _make_jobkorea_html([{"href": "/Recruit/GNo=1", "title": "잡코리아공고", "company": "회사A", "tags": []}])
    li_html = _make_linkedin_html([{"uid": "222", "title": "LinkedIn Job", "company": "CorpC"}])
    rp_data = _make_rocketpunch_json([{"id": 1, "position": "개발자", "company": "스타트업", "skills": []}])

    def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.url = url
        if "jobkorea" in url:
            resp.text = jk_html
        elif "linkedin" in url:
            resp.text = li_html
        elif "rocketpunch" in url:
            resp.json.return_value = rp_data
        return resp

    with patch("requests.get", side_effect=mock_get):
        result = crawl_all(["테스트"], selected_sites)

    site_source_map = {
        "jobkorea": "잡코리아",
        "linkedin": "링크드인",
        "rocketpunch": "로켓펀치",
    }
    allowed_sources = {site_source_map[s] for s in selected_sites}
    for job in result:
        assert job["source"] in allowed_sources, (
            f"허용되지 않은 source: {job['source']} (허용: {allowed_sources})"
        )
