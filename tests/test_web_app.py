"""
통합 테스트: web_app.py FastAPI 엔드포인트
Feature: job-crawler-web-ui
Requirements: 1.1~1.4, 4.1, 4.2, 5.2, 6.2
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

import web_app
from web_app import app


client = TestClient(app)


# ── 요구사항 6.2: app이 FastAPI 인스턴스인지 확인 ─────────────────────────────
def test_app_is_fastapi_instance():
    """app 변수가 FastAPI 인스턴스인지 확인 (Requirements 6.2)"""
    assert isinstance(app, FastAPI)


# ── 요구사항 1.1~1.4: GET / 응답 확인 ────────────────────────────────────────
def test_get_root_returns_200():
    """GET / 응답이 200이어야 한다 (Requirements 1.1)"""
    response = client.get("/")
    assert response.status_code == 200


def test_get_root_contains_form():
    """GET / 응답에 검색 폼 요소가 포함되어야 한다 (Requirements 1.1, 1.2)"""
    response = client.get("/")
    html = response.text
    # 폼 존재 확인
    assert '<form' in html
    assert 'action="/search"' in html
    # 키워드 입력 필드 확인
    assert 'name="keywords"' in html


def test_get_root_contains_site_checkboxes():
    """GET / 응답에 5개 사이트 체크박스가 포함되어야 한다 (Requirements 1.3)"""
    response = client.get("/")
    html = response.text
    for site in ["saramin", "wanted", "jobkorea", "linkedin", "rocketpunch"]:
        assert f'value="{site}"' in html, f"사이트 체크박스 누락: {site}"


def test_get_root_all_sites_checked_by_default():
    """GET / 응답에서 모든 사이트가 기본 선택 상태여야 한다 (Requirements 1.4)"""
    response = client.get("/")
    html = response.text
    # 각 사이트 체크박스가 checked 상태인지 확인
    for site in ["saramin", "wanted", "jobkorea", "linkedin", "rocketpunch"]:
        assert f'value="{site}"' in html
    # checked 속성이 존재하는지 확인 (모든 사이트가 기본 선택)
    assert html.count("checked") >= 5


# ── 요구사항 4.1: 빈 키워드 시 오류 메시지 ───────────────────────────────────
def test_post_search_empty_keyword_returns_error():
    """POST /search 빈 키워드 제출 시 오류 메시지가 표시되어야 한다 (Requirements 4.1)"""
    response = client.post("/search", data={"keywords": "", "sites": ["saramin"]})
    assert response.status_code == 200
    assert "키워드를 입력해주세요." in response.text


def test_post_search_whitespace_keyword_returns_error():
    """POST /search 공백만 있는 키워드 제출 시 오류 메시지가 표시되어야 한다 (Requirements 4.1, 4.3)"""
    response = client.post("/search", data={"keywords": "   ", "sites": ["saramin"]})
    assert response.status_code == 200
    assert "키워드를 입력해주세요." in response.text


# ── 요구사항 4.2: 사이트 미선택 시 오류 메시지 ───────────────────────────────
def test_post_search_no_sites_returns_error():
    """POST /search 사이트 미선택 시 오류 메시지가 표시되어야 한다 (Requirements 4.2)"""
    response = client.post("/search", data={"keywords": "Python"})
    assert response.status_code == 200
    assert "최소 1개의 사이트를 선택해주세요." in response.text


# ── 요구사항 5.2: 모든 사이트 실패(결과 0건) 시 오류 메시지 ──────────────────
def test_post_search_crawl_all_empty_returns_error_message():
    """POST /search에서 crawl_all이 빈 리스트를 반환하면 오류 메시지가 표시되어야 한다 (Requirements 5.2)"""
    with patch("web_app.crawl_all", return_value=[]) as mock_crawl, \
         patch("web_app.apply_filter", return_value=[]) as mock_filter:
        response = client.post(
            "/search",
            data={"keywords": "Python", "sites": ["saramin", "wanted"]},
        )

    assert response.status_code == 200
    assert "크롤링 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요." in response.text
    mock_crawl.assert_called_once()
    mock_filter.assert_called_once()


def test_post_search_crawl_all_empty_does_not_show_no_results_message():
    """crawl_all 빈 리스트 반환 시 '검색 결과가 없습니다.' 대신 크롤링 오류 메시지가 표시되어야 한다"""
    with patch("web_app.crawl_all", return_value=[]), \
         patch("web_app.apply_filter", return_value=[]):
        response = client.post(
            "/search",
            data={"keywords": "Python", "sites": ["saramin"]},
        )

    html = response.text
    assert "크롤링 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요." in html


def test_post_search_with_results_no_error_message():
    """crawl_all이 결과를 반환하면 크롤링 오류 메시지가 표시되지 않아야 한다"""
    mock_jobs = [
        {
            "id": "saramin_1",
            "title": "Python 개발자",
            "company": "테스트회사",
            "url": "https://example.com/job/1",
            "tags": "Python Django",
            "source": "사람인",
        }
    ]
    with patch("web_app.crawl_all", return_value=mock_jobs), \
         patch("web_app.apply_filter", return_value=mock_jobs):
        response = client.post(
            "/search",
            data={"keywords": "Python", "sites": ["saramin"]},
        )

    assert response.status_code == 200
    assert "크롤링 중 오류가 발생했습니다." not in response.text
