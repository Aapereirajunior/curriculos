import re

from auto_jobs.config import SearchConfig
from auto_jobs.models import JobPosting


def strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()


def matches_search(job: JobPosting, search: SearchConfig) -> bool:
    haystack = f"{job.title} {job.location} {job.description_text}".lower()

    if search.keywords and not any(k.lower() in haystack for k in search.keywords):
        return False

    if search.locations and not any(
        loc.lower() in job.location.lower() for loc in search.locations
    ):
        return False

    if any(k.lower() in haystack for k in search.exclude_keywords):
        return False

    return True
