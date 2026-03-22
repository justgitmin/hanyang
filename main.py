import schedule
import time
from crawler import crawl_all
from filter import apply_filter
from storage import filter_new_jobs
from slack import send_slack_message
from config import KEYWORDS, SITES, SCHEDULE_INTERVAL_MINUTES


def run_job():
    print(f"\n[실행] 채용공고 수집 시작...")

    # 1. 크롤링
    jobs = crawl_all(KEYWORDS, SITES)
    print(f"  수집된 공고: {len(jobs)}건")

    # 2. 키워드 필터링
    filtered = apply_filter(jobs)
    print(f"  필터링 후: {len(filtered)}건")

    # 3. 중복 제거
    new_jobs = filter_new_jobs(filtered)
    print(f"  신규 공고: {len(new_jobs)}건")

    # 4. Slack 전송
    send_slack_message(new_jobs)


if __name__ == "__main__":
    print(f"채용 공고 크롤러 시작 (주기: {SCHEDULE_INTERVAL_MINUTES}분)")
    print(f"키워드: {KEYWORDS}")
    print(f"대상 사이트: {SITES}")

    # 시작 시 즉시 1회 실행
    run_job()

    # 이후 주기적 실행
    schedule.every(SCHEDULE_INTERVAL_MINUTES).minutes.do(run_job)

    while True:
        schedule.run_pending()
        time.sleep(30)
