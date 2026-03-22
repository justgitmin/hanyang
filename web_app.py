import re

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from crawler import crawl_all
from filter import apply_filter

app = FastAPI()
templates = Jinja2Templates(directory="templates")

ALL_SITES = ["saramin", "wanted", "jobkorea", "linkedin", "rocketpunch"]


def parse_keywords(raw: str) -> list[str]:
    """쉼표 또는 공백으로 구분된 키워드 문자열을 파싱하여 토큰 리스트를 반환한다."""
    tokens = re.split(r"[,\s]+", raw)
    return [t.strip() for t in tokens if t.strip()]


def validate_input(keywords_raw: str, sites: list[str]) -> str | None:
    """입력 유효성 검사. 오류가 있으면 오류 메시지를 반환하고, 없으면 None을 반환한다."""
    if not parse_keywords(keywords_raw):
        return "키워드를 입력해주세요."
    if not sites:
        return "최소 1개의 사이트를 선택해주세요."
    return None


@app.get("/", response_class=HTMLResponse)
async def search_page(request: Request) -> HTMLResponse:
    """검색 폼 페이지 반환. 모든 사이트 기본 선택."""
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "jobs": [],
            "keywords_input": "",
            "selected_sites": ALL_SITES,
            "error": None,
            "searched": False,
            "all_sites": ALL_SITES,
        },
    )


@app.post("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    keywords: str = Form(""),
    sites: list[str] = Form(default=[]),
) -> HTMLResponse:
    """크롤링 실행 후 결과 페이지 반환."""
    error = validate_input(keywords, sites)
    if error:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "jobs": [],
                "keywords_input": keywords,
                "selected_sites": sites,
                "error": error,
                "searched": False,
                "all_sites": ALL_SITES,
            },
        )

    keyword_list = parse_keywords(keywords)
    raw_jobs = crawl_all(keyword_list, sites)
    jobs = apply_filter(raw_jobs, keyword_list)

    error_msg = None
    if not raw_jobs:
        error_msg = "크롤링 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "jobs": jobs,
            "keywords_input": keywords,
            "selected_sites": sites,
            "error": error_msg,
            "searched": True,
            "all_sites": ALL_SITES,
        },
    )
