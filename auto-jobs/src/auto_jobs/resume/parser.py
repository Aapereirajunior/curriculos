from pathlib import Path

import yaml


def load_base_resume(path: str) -> dict:
    """Carrega o currículo base estruturado (YAML). Veja data/resume_base.yaml."""
    resume_path = Path(path)
    if not resume_path.exists():
        raise FileNotFoundError(
            f"Currículo base não encontrado em '{path}'. Copie e edite "
            f"data/resume_base.yaml com seus dados reais."
        )
    with resume_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
