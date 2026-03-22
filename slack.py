import requests
import json
from config import SLACK_WEBHOOK_URL


def send_slack_message(jobs: list[dict]):
    """새 채용공고를 Slack으로 전송"""
    if not SLACK_WEBHOOK_URL:
        print("[Slack] SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        return

    if not jobs:
        print("[Slack] 새로운 공고 없음, 전송 생략")
        return

    # 최대 10개씩 묶어서 전송 (Slack 메시지 길이 제한 대비)
    for i in range(0, len(jobs), 10):
        chunk = jobs[i:i + 10]
        blocks = _build_blocks(chunk, i)
        payload = {"blocks": blocks}

        try:
            res = requests.post(
                SLACK_WEBHOOK_URL,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            res.raise_for_status()
            print(f"[Slack] {len(chunk)}개 공고 전송 완료")
        except Exception as e:
            print(f"[Slack 전송 오류] {e}")


def _build_blocks(jobs: list[dict], offset: int) -> list:
    blocks = []

    if offset == 0:
        blocks.append({
            "type": "header",
            "text": {"type": "plain_text", "text": f"📋 새 채용공고 {len(jobs)}건"},
        })

    for job in jobs:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*<{job['url']}|{job['title']}>*\n"
                    f"🏢 {job['company']}  |  🔖 {job['source']}\n"
                    f"🏷️ {job['tags'] or '태그 없음'}"
                ),
            },
        })

    return blocks
