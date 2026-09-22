"""Cliente para a API pública do Greenhouse Job Board.

Documentação: https://developers.greenhouse.io/job-board.html
Endpoint usado é somente leitura e público, não requer autenticação.
"""

import logging

import requests

from auto_jobs.config import SearchConfig
from auto_jobs.models import JobPosting
from auto_jobs.sources.base import matches_search, strip_html

logger = logging.getLogger(__name__)

API_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"


def fetch_jobs(company_token: str, search: SearchConfig, limit: int = 20) -> list[JobPosting]:
    """Busca vagas abertas de uma empresa no Greenhouse e filtra pelos critérios."""
    url = API_URL.format(token=company_token)
    try:
        resp = requests.get(url, params={"content": "true"}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Falha ao buscar vagas do Greenhouse para '%s': %s", company_token, exc)
        return []

    jobs_raw = resp.json().get("jobs", [])
    postings: list[JobPosting] = []

    for job in jobs_raw:
        location = (job.get("location") or {}).get("name", "")
        description_html = job.get("content", "")
        posting = JobPosting(
            source="greenhouse",
            company=company_token,
            job_id=str(job["id"]),
            title=job.get("title", ""),
            location=location,
            url=job.get("absolute_url", ""),
            description_html=description_html,
            description_text=strip_html(description_html),
        )
        if matches_search(posting, search):
            postings.append(posting)
        if len(postings) >= limit:
            break

    return postings
