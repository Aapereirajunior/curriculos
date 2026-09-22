import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

from auto_jobs.models import Candidate

load_dotenv()


@dataclass
class SearchConfig:
    keywords: list[str]
    locations: list[str]
    exclude_keywords: list[str]
    max_results_per_company: int


@dataclass
class ApplicationConfig:
    mode: str
    dry_run: bool
    max_applications_per_run: int
    cover_letter: bool
    default_answers: dict[str, str] = field(default_factory=dict)


@dataclass
class AppConfig:
    search: SearchConfig
    companies_greenhouse: list[str]
    companies_lever: list[str]
    candidate: Candidate
    application: ApplicationConfig
    anthropic_api_key: str
    root_dir: Path


def load_config(path: str = "config.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config não encontrada em '{path}'. Copie config.example.yaml para "
            f"config.yaml e preencha com seus dados."
        )

    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    root_dir = config_path.resolve().parent

    search = SearchConfig(
        keywords=raw["search"]["keywords"],
        locations=raw["search"].get("locations", []),
        exclude_keywords=raw["search"].get("exclude_keywords", []),
        max_results_per_company=raw["search"].get("max_results_per_company", 20),
    )

    candidate_raw = raw["candidate"]
    candidate = Candidate(
        full_name=candidate_raw["full_name"],
        email=candidate_raw["email"],
        phone=candidate_raw["phone"],
        linkedin_url=candidate_raw.get("linkedin_url", ""),
        resume_path=str(root_dir / candidate_raw["resume_path"]),
        resume_file_to_upload=str(root_dir / candidate_raw["resume_file_to_upload"]),
    )

    application = ApplicationConfig(
        mode=raw["application"].get("mode", "review"),
        dry_run=raw["application"].get("dry_run", True),
        max_applications_per_run=raw["application"].get("max_applications_per_run", 10),
        cover_letter=raw["application"].get("cover_letter", True),
        default_answers=raw["application"].get("default_answers", {}),
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    return AppConfig(
        search=search,
        companies_greenhouse=raw.get("companies", {}).get("greenhouse", []),
        companies_lever=raw.get("companies", {}).get("lever", []),
        candidate=candidate,
        application=application,
        anthropic_api_key=api_key,
        root_dir=root_dir,
    )
