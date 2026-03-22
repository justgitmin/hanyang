import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def crawl_saramin(keyword: str) -> list[dict]:
    """사람인 채용공고 크롤링"""
    jobs = []
    url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword={keyword}&recruitPage=1"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for item in soup.select(".item_recruit"):
            title_tag = item.select_one(".job_tit a")
            company_tag = item.select_one(".corp_name a")
            tags = [t.text.strip() for t in item.select(".job_sector span")]

            if not title_tag:
                continue

            job_id = f"saramin_{title_tag.get('href', '').split('rec_idx=')[-1].split('&')[0]}"
            jobs.append({
                "id": job_id,
                "title": title_tag.text.strip(),
                "company": company_tag.text.strip() if company_tag else "알 수 없음",
                "url": "https://www.saramin.co.kr" + title_tag.get("href", ""),
                "tags": " ".join(tags),
                "source": "사람인",
            })
    except Exception as e:
        print(f"[사람인 크롤링 오류] {e}")

    return jobs


def crawl_wanted(keyword: str) -> list[dict]:
    """원티드 API 크롤링"""
    jobs = []
    url = "https://www.wanted.co.kr/api/v4/jobs"
    params = {
        "country": "kr",
        "job_sort": "job.latest_order",
        "locations": "all",
        "years": -1,
        "limit": 20,
        "offset": 0,
        "tag_type_ids": "",
        "keyword": keyword,
    }

    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        for item in data.get("data", []):
            job_id = f"wanted_{item['id']}"
            jobs.append({
                "id": job_id,
                "title": item.get("position", ""),
                "company": item.get("company", {}).get("name", "알 수 없음"),
                "url": f"https://www.wanted.co.kr/wd/{item['id']}",
                "tags": " ".join(item.get("tags", [])),
                "source": "원티드",
            })
    except Exception as e:
        print(f"[원티드 크롤링 오류] {e}")

    return jobs


def crawl_jobkorea(keyword: str) -> list[dict]:
    """잡코리아 채용공고 크롤링"""
    jobs = []
    url = f"https://www.jobkorea.co.kr/Search/?stext={keyword}"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for item in soup.select(".list-post .post-list-info"):
            title_tag = item.select_one(".title a")
            company_tag = item.select_one(".name a")
            tags = [t.text.strip() for t in item.select(".chip-information-group .chip")]

            if not title_tag:
                continue

            href = title_tag.get("href", "")
            # GNo 파라미터 또는 href 경로에서 고유 식별자 추출
            gno = ""
            if "GNo=" in href:
                gno = href.split("GNo=")[-1].split("&")[0]
            elif href:
                gno = href.strip("/").split("/")[-1]

            job_id = f"jobkorea_{gno}" if gno else f"jobkorea_{title_tag.text.strip()}"

            full_url = href if href.startswith("http") else "https://www.jobkorea.co.kr" + href

            jobs.append({
                "id": job_id,
                "title": title_tag.text.strip() or "",
                "company": (company_tag.text.strip() if company_tag else "") or "",
                "url": full_url or "",
                "tags": " ".join(tags) or "",
                "source": "잡코리아",
            })
    except Exception as e:
        print(f"[잡코리아 크롤링 오류] {e}")

    return jobs


def crawl_linkedin(keyword: str) -> list[dict]:
    """링크드인 채용공고 크롤링"""
    jobs = []
    url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location=Korea"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()

        # 로그인 리다이렉트 감지
        if "authwall" in res.url or "login" in res.url or "signup" in res.url:
            return []

        soup = BeautifulSoup(res.text, "html.parser")

        for item in soup.select(".jobs-search__results-list li"):
            title_tag = item.select_one(".base-search-card__title")
            company_tag = item.select_one(".base-search-card__subtitle")
            link_tag = item.select_one("a.base-card__full-link") or item.select_one("a")

            href = (link_tag.get("href", "") if link_tag else "") or ""

            # data-entity-urn 또는 링크 숫자 ID로 고유 식별자 추출
            entity_urn = item.get("data-entity-urn", "")
            if entity_urn:
                job_uid = entity_urn.split(":")[-1]
            else:
                # URL에서 숫자 ID 추출 (예: /jobs/view/1234567890/)
                match = re.search(r"/jobs/view/(\d+)", href)
                job_uid = match.group(1) if match else href.strip("/").split("/")[-1].split("?")[0]

            jobs.append({
                "id": f"linkedin_{job_uid}",
                "title": (title_tag.text.strip() if title_tag else "") or "",
                "company": (company_tag.text.strip() if company_tag else "") or "",
                "url": href or "",
                "tags": "",
                "source": "링크드인",
            })
    except Exception as e:
        print(f"[링크드인 크롤링 오류] {e}")

    return jobs


def crawl_rocketpunch(keyword: str) -> list[dict]:
    """로켓펀치 채용공고 크롤링 (JSON API)"""
    jobs = []
    url = f"https://www.rocketpunch.com/api/jobs/search?keywords={keyword}"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()

        for item in data.get("data", {}).get("results", []):
            job_id = f"rocketpunch_{item['id']}"
            jobs.append({
                "id": job_id,
                "title": item.get("position", "") or "",
                "company": item.get("company", {}).get("name", "") or "",
                "url": f"https://www.rocketpunch.com/jobs/{item.get('id', '')}" or "",
                "tags": " ".join(item.get("skills", []) or []) or "",
                "source": "로켓펀치",
            })
    except Exception as e:
        print(f"[로켓펀치 크롤링 오류] {e}")

    return jobs


def crawl_all(keywords: list[str], sites: list[str]) -> list[dict]:
    """모든 사이트에서 키워드별 크롤링 후 합산"""
    all_jobs = []
    seen_ids = set()

    for keyword in keywords:
        if "saramin" in sites:
            for job in crawl_saramin(keyword):
                if job["id"] not in seen_ids:
                    all_jobs.append(job)
                    seen_ids.add(job["id"])

        if "wanted" in sites:
            for job in crawl_wanted(keyword):
                if job["id"] not in seen_ids:
                    all_jobs.append(job)
                    seen_ids.add(job["id"])

        if "jobkorea" in sites:
            for job in crawl_jobkorea(keyword):
                if job["id"] not in seen_ids:
                    all_jobs.append(job)
                    seen_ids.add(job["id"])

        if "linkedin" in sites:
            for job in crawl_linkedin(keyword):
                if job["id"] not in seen_ids:
                    all_jobs.append(job)
                    seen_ids.add(job["id"])

        if "rocketpunch" in sites:
            for job in crawl_rocketpunch(keyword):
                if job["id"] not in seen_ids:
                    all_jobs.append(job)
                    seen_ids.add(job["id"])

    return all_jobs
