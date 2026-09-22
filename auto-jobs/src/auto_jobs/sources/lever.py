"""Cliente para a API pública do Lever Postings.

Documentação: https://github.com/lever/postings-api
Endpoint usado é somente leitura e público, não requer autenticação.
"""

import logging

import requests

from auto_jobs.config import SearchConfig
from auto_jobs.models import JobPosting
from auto_jobs.sources.base import matches_search, strip_html

logger = logging.getLogger(__name__)

API_URL = "https://api.lever.co/v0/postings/{token}"


def fetch_jobs(company_token: str, search: SearchConfig, limit: int = 20) -> list[JobPosting]:
    """Busca vagas abertas de uma empresa no Lever e filtra pelos critérios."""
    url = API_URL.format(token=company_token)
    try:
        resp = requests.get(url, params={"mode": "json"}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Falha ao buscar vagas do Lever para '%s': %s", company_token, exc)
        return []

    jobs_raw = resp.json()
    postings: list[JobPosting] = []

    for job in jobs_raw:
        categories = job.get("categories", {})
        location = categories.get("location", "")
        description_html = job.get("descriptionPlain", "") or job.get("description", "")
        posting = JobPosting(
            source="lever",
            company=company_token,
            job_id=job["id"],
            title=job.get("text", ""),
            location=location,
            url=job.get("hostedUrl", ""),
            description_html=description_html,
            description_text=strip_html(description_html),
        )
        if matches_search(posting, search):
            postings.append(posting)
        if len(postings) >= limit:
            break

    return postings
