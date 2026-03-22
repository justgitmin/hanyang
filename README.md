# Job Crawler

채용 사이트에서 공고를 자동으로 수집하여 Slack으로 알림을 보내거나, 웹 UI에서 직접 검색할 수 있는 도구입니다.

## 지원 사이트

- 사람인
- 원티드
- 잡코리아
- 링크드인
- 로켓펀치

## 설치

```bash
pip install -r requirements.txt
```

## 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 Slack 웹훅 주소를 입력합니다.

```bash
cp .env.example .env
```

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
```

`config.py`에서 키워드, 사이트, 스케줄 간격을 설정합니다.

```python
KEYWORDS = ["Python", "백엔드", "Django", "FastAPI"]
EXCLUDE_KEYWORDS = ["신입 불가", "경력 10년"]
SITES = ["saramin", "wanted", "jobkorea", "linkedin", "rocketpunch"]
SCHEDULE_INTERVAL_MINUTES = 60
```

## 사용법

### 스케줄러 (Slack 알림)

주기적으로 크롤링하여 새 공고를 Slack으로 전송합니다.

```bash
python main.py
```

### 웹 UI

브라우저에서 키워드를 입력하여 즉시 검색합니다.

```bash
uvicorn web_app:app --reload
```

`http://localhost:8000` 접속

## 테스트

```bash
pytest tests/ --tb=short
```

## 파일 구조

```
job-crawler/
├── main.py          # 스케줄러 진입점
├── web_app.py       # 웹 UI (FastAPI)
├── crawler.py       # 사이트별 크롤러
├── filter.py        # 키워드 필터링
├── slack.py         # Slack 전송
├── storage.py       # 중복 공고 관리
├── config.py        # 설정
├── templates/
│   └── index.html   # 웹 UI 템플릿
└── tests/           # 테스트
```
