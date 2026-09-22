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
    do Greenhouse. Retorna True se o envio foi concluído (ou simulado com sucesso)."""

    name_parts = candidate.full_name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(job.url, wait_until="networkidle", timeout=30000)

            fill_text_field(page, "First Name", first_name)
            fill_text_field(page, "Last Name", last_name)
            fill_text_field(page, "Email", candidate.email)
            fill_text_field(page, "Phone", candidate.phone)

            upload_file_field(page, "Resume", candidate.resume_file_to_upload)
            if tailored.cover_letter_docx_path:
                upload_file_field(page, "Cover Letter", tailored.cover_letter_docx_path)

            answer_default_questions(page, default_answers)

            if dry_run:
                logger.info("[dry-run] Formulário preenchido para %s, envio NÃO realizado.", job.key)
                return True

            submit_button = page.get_by_role("button", name="Submit Application")
            if submit_button.count() == 0:
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
