import json
import os
from config import SEEN_JOBS_FILE


def load_seen_jobs() -> set:
    if not os.path.exists(SEEN_JOBS_FILE):
        return set()
    with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_seen_jobs(seen: set):
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False)


def filter_new_jobs(jobs: list[dict]) -> list[dict]:
    """이미 본 공고를 제거하고, 새 공고를 저장소에 추가"""
    seen = load_seen_jobs()
    new_jobs = [j for j in jobs if j["id"] not in seen]
    seen.update(j["id"] for j in new_jobs)
    save_seen_jobs(seen)
    return new_jobs
