from dataclasses import dataclass, field


@dataclass
class JobPosting:
    source: str          # "greenhouse" ou "lever"
    company: str         # token/slug da empresa
    job_id: str
    title: str
    location: str
    url: str
    description_html: str = ""
    description_text: str = ""

    @property
    def key(self) -> str:
        return f"{self.source}:{self.company}:{self.job_id}"


@dataclass
class TailoredApplication:
    job: JobPosting
    summary: str
    tailored_bullets: dict[str, list[str]]  # empresa -> bullets adaptados
    cover_letter: str
    resume_docx_path: str = ""
    cover_letter_docx_path: str = ""


@dataclass
class Candidate:
    full_name: str
    email: str
    phone: str
    linkedin_url: str
    resume_path: str
    resume_file_to_upload: str
