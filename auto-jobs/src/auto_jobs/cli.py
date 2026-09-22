import logging

import click

from auto_jobs.apply import greenhouse_apply, lever_apply
from auto_jobs.config import load_config
from auto_jobs.resume.parser import load_base_resume
from auto_jobs.resume.render import render_cover_letter_docx, render_resume_docx
from auto_jobs.resume.tailor import tailor_application
from auto_jobs.sources import greenhouse, lever
from auto_jobs.tracker import Tracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("auto_jobs")


def _search_jobs(config):
    jobs = []
    for token in config.companies_greenhouse:
        jobs += greenhouse.fetch_jobs(token, config.search, config.search.max_results_per_company)
    for token in config.companies_lever:
        jobs += lever.fetch_jobs(token, config.search, config.search.max_results_per_company)
    return jobs


@click.group()
@click.option("--config", "config_path", default="config.yaml", help="Caminho do config.yaml")
@click.pass_context
def cli(ctx, config_path):
    """Auto-Jobs: busca vagas, adapta seu currículo com IA e candidata-se automaticamente."""
    ctx.ensure_object(dict)
    config = load_config(config_path)
    ctx.obj["config"] = config
    ctx.obj["tracker"] = Tracker(str(config.root_dir / "data" / "applications.db"))


@cli.command()
@click.pass_context
def search(ctx):
    """Busca vagas novas nas empresas configuradas e mostra na tela."""
    config = ctx.obj["config"]
    tracker = ctx.obj["tracker"]

    jobs = _search_jobs(config)
    new_jobs = [j for j in jobs if not tracker.already_seen(j)]

    click.echo(f"Encontradas {len(jobs)} vagas, {len(new_jobs)} novas.")
    for job in new_jobs:
        tracker.record(job, status="found")
        click.echo(f"  [{job.source}] {job.company} — {job.title} ({job.location}) -> {job.url}")


@cli.command()
@click.option("--limit", default=None, type=int, help="Número máximo de candidaturas nesta execução")
@click.pass_context
def run(ctx, limit):
    """Pipeline completo: busca vagas novas, adapta currículo e candidata-se
    (respeitando dry_run e o modo configurado em application.mode)."""
    config = ctx.obj["config"]
    tracker = ctx.obj["tracker"]

    base_resume = load_base_resume(config.candidate.resume_path)
    jobs = _search_jobs(config)
    new_jobs = [j for j in jobs if not tracker.already_seen(j)]

    max_apps = limit or config.application.max_applications_per_run
    already_today = tracker.count_applied_today()
    remaining_quota = max(max_apps - already_today, 0)

    click.echo(f"{len(new_jobs)} vagas novas encontradas. Cota restante hoje: {remaining_quota}.")

    applied_count = 0
    for job in new_jobs:
        if applied_count >= remaining_quota:
            click.echo("Cota de candidaturas atingida para esta execução.")
            break

        tracker.record(job, status="found")

        try:
            tailored = tailor_application(job, base_resume, config.anthropic_api_key)
        except Exception as exc:  # noqa: BLE001
            logger.error("Falha ao adaptar currículo para %s: %s", job.key, exc)
            tracker.update_status(job, "tailor_failed")
            continue

        out_dir = str(config.root_dir / "data" / "generated")
        tailored.resume_docx_path = render_resume_docx(base_resume, tailored, out_dir)
        if config.application.cover_letter:
            tailored.cover_letter_docx_path = render_cover_letter_docx(tailored, out_dir)
        tracker.update_status(job, "tailored")

        if config.application.mode != "auto":
            click.echo(f"[review] Candidatura preparada para {job.key}: {tailored.resume_docx_path}")
            continue

        applier = greenhouse_apply if job.source == "greenhouse" else lever_apply
        success = applier.submit_application(
            job=job,
            tailored=tailored,
            candidate=config.candidate,
            default_answers=config.application.default_answers,
            dry_run=config.application.dry_run,
        )

        if success:
            status = "dry_run_ok" if config.application.dry_run else "applied"
            tracker.update_status(job, status)
            applied_count += 1
            click.echo(f"[{status}] {job.key} — {job.title} @ {job.company}")
        else:
            tracker.update_status(job, "apply_failed")
            click.echo(f"[apply_failed] {job.key}")


if __name__ == "__main__":
    cli()
