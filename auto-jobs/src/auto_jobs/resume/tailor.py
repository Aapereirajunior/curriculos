import json
import logging
import os

from anthropic import Anthropic

from auto_jobs.models import JobPosting, TailoredApplication

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

SYSTEM_PROMPT = """Você é um assistente que adapta currículos e escreve cartas de \
apresentação curtas e objetivas para candidaturas de emprego. Nunca invente \
experiências, empresas, cargos ou números que não estejam no currículo base \
fornecido — apenas reordene, reformule e priorize o que já existe para dar \
mais destaque ao que é relevante para a vaga. Responda SEMPRE em JSON válido, \
sem nenhum texto fora do JSON."""

USER_PROMPT_TEMPLATE = """Currículo base (JSON):
{resume_json}

Vaga (empresa: {company}, título: {title}):
{description}

Gere um JSON com exatamente estas chaves:
- "summary": um resumo profissional de 2-4 frases adaptado para esta vaga.
- "bullets_by_company": objeto onde cada chave é o nome da empresa (igual ao \
currículo base) e o valor é uma lista de bullets reformulados/priorizados \
(mesmo conteúdo do currículo base, sem inventar fatos novos).
- "cover_letter": uma carta de apresentação curta (máximo 200 palavras), em \
português, mencionando a empresa e a vaga pelo nome.
"""


def tailor_application(
    job: JobPosting, base_resume: dict, api_key: str, model: str = DEFAULT_MODEL
) -> TailoredApplication:
    client = Anthropic(api_key=api_key)

    prompt = USER_PROMPT_TEMPLATE.format(
        resume_json=json.dumps(base_resume, ensure_ascii=False, indent=2),
        company=job.company,
        title=job.title,
        description=job.description_text[:6000],
    )

    message = client.messages.create(
        model=model,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.error("Resposta do modelo não é JSON válido para vaga %s: %s", job.key, raw_text)
        raise

    return TailoredApplication(
        job=job,
        summary=data.get("summary", ""),
        tailored_bullets=data.get("bullets_by_company", {}),
        cover_letter=data.get("cover_letter", ""),
    )
