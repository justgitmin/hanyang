import os
from dotenv import load_dotenv

load_dotenv()

# Slack 설정
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# 검색 키워드 (OR 조건)
KEYWORDS = [
    "Python",
    "백엔드",
    "Django",
    "FastAPI",
]

# 제외 키워드 (포함 시 필터링)
EXCLUDE_KEYWORDS = [
    "신입 불가",
    "경력 10년",
]

# 크롤링 대상 사이트
# 유효한 식별자: "saramin", "wanted", "jobkorea", "linkedin", "rocketpunch"
SITES = ["saramin", "wanted", "jobkorea", "linkedin", "rocketpunch"]

# 스케줄 간격 (분)
SCHEDULE_INTERVAL_MINUTES = 60

# 저장소 파일 경로
SEEN_JOBS_FILE = "seen_jobs.json"
