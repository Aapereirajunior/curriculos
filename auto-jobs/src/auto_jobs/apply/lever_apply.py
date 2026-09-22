import logging
from pathlib import Path

from playwright.sync_api import sync_playwright

from auto_jobs.apply.base import answer_default_questions, fill_text_field, upload_file_field
from auto_jobs.models import Candidate, JobPosting, TailoredApplication

logger = logging.getLogger(__name__)


def submit_application(
    job: JobPosting,
    tailored: TailoredApplication,
    candidate: Candidate,
    default_answers: dict[str, str],
    dry_run: bool = True,
    screenshot_dir: str = "data/screenshots",
) -> bool:
    """Preenche e (se dry_run=False) envia a candidatura no formulário hospedado
    do Lever (<job_url>/apply). Retorna True se o envio foi concluído (ou
    simulado com sucesso)."""

    apply_url = job.url.rstrip("/") + "/apply"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(apply_url, wait_until="networkidle", timeout=30000)

            fill_text_field(page, "Full name", candidate.full_name)
            fill_text_field(page, "Email", candidate.email)
            fill_text_field(page, "Phone", candidate.phone)
            fill_text_field(page, "Current location", "")

            upload_file_field(page, "Resume/CV", candidate.resume_file_to_upload)
            fill_text_field(page, "Additional Information", tailored.cover_letter)

            answer_default_questions(page, default_answers)

            if dry_run:
                logger.info("[dry-run] Formulário preenchido para %s, envio NÃO realizado.", job.key)
                return True

            submit_button = page.get_by_role("button", name="Submit application")
            submit_button.first.click()
            page.wait_for_load_state("networkidle", timeout=30000)
            return True

        except Exception as exc:  # noqa: BLE001
            logger.error("Falha ao candidatar-se em %s: %s", job.key, exc)
            Path(screenshot_dir).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=f"{screenshot_dir}/error_{job.company}_{job.job_id}.png")
            return False
        finally:
            browser.close()
