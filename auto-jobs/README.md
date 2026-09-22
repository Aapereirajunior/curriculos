# Auto-Jobs

Automação para busca de vagas, adaptação de currículo com IA e envio de
candidaturas, focada em empresas que usam **Greenhouse** e **Lever** como
ATS (Applicant Tracking System) — ambos expõem APIs públicas de leitura de
vagas, o que torna a busca segura e estável (sem scraping frágil).

## ⚠️ Leia antes de usar

- O envio automático (`application.mode: auto`) preenche e submete
  formulários reais de candidatura via navegador (Playwright). Comece
  **sempre** com `application.dry_run: true` para revisar o preenchimento
  antes de desativar essa proteção.
- Cada empresa customiza seu formulário (perguntas de triagem diferentes),
  então nem todo campo será preenchido automaticamente — revise os logs.
- Automação de candidaturas em **LinkedIn/Indeed não é suportada** aqui de
  propósito: exige login e viola os Termos de Uso dessas plataformas,
  podendo levar ao banimento da sua conta.
- Este repositório é privado, mas `data/resume_base.yaml`, `data/resume_base.docx`
  e `config.yaml` já contêm/conterão seus dados pessoais reais (nome, e-mail,
  telefone, Lattes, ORCID) — não torne o repo público sem remover/gitignorar
  esses arquivos.
- Greenhouse/Lever são fortes em vagas de tecnologia. Organismos como
  **OPAS/OMS, ONU e a própria Fiocruz normalmente não usam esses ATS** —
  publicam em portais próprios (careers.who.int, paho.org/jobs, concursos
  Fiocruz). Para essas vagas, use `tailor_application()` manualmente (cole a
  descrição da vaga) para gerar currículo/carta adaptados, mas a busca e o
  envio automáticos deste projeto não alcançam esses portais.
- **Indeed, LinkedIn Jobs e Glassdoor bloqueiam acesso automatizado**
  (retornam HTTP 403/999 a requisições de bot) — testado na prática. Sites
  agregadores como Jooble costumam responder, mas isso é para pesquisa
  manual pontual (ex: pedir para o assistente de IA buscar "vagas X em Y"),
  não algo que este projeto automatiza de forma recorrente/confiável.

## Como funciona

1. **Busca**: consulta as APIs públicas do Greenhouse
   (`boards-api.greenhouse.io`) e do Lever (`api.lever.co`) para as empresas
   configuradas, filtrando por palavra-chave/localização.
2. **Adaptação**: envia seu currículo base + a descrição da vaga para a API
   da Anthropic, que gera um resumo profissional e bullets priorizados para
   aquela vaga específica (sem inventar experiência) e uma carta de
   apresentação curta.
3. **Geração**: renderiza currículo e carta adaptados em `.docx`.
4. **Envio**: usa Playwright para preencher (e, fora do modo dry-run,
   enviar) o formulário de candidatura hospedado pela empresa.
5. **Tracker**: um SQLite local (`data/applications.db`) evita candidatar-se
   duas vezes à mesma vaga e limita quantas candidaturas são enviadas por
   dia (`application.max_applications_per_run`).

## Setup

```bash
cd auto-jobs
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env            # adicione sua ANTHROPIC_API_KEY
cp config.example.yaml config.yaml   # edite com seus dados e empresas-alvo
```

Edite também `data/resume_base.yaml` com seu currículo real (experiências,
skills, educação) — é a fonte de verdade usada pela IA para adaptar cada
candidatura. Coloque o arquivo do seu currículo atual (para upload) em
`data/resume_base.docx` ou aponte `candidate.resume_file_to_upload` no
`config.yaml` para o caminho correto.

## Uso

```bash
# Só lista vagas novas encontradas, sem gerar nada
python -m auto_jobs.cli search

# Pipeline completo: busca, adapta currículo, gera docx e (se mode=auto e
# dry_run=false) envia a candidatura
python -m auto_jobs.cli run --limit 5
```

Ou, após `pip install -e .`, use o comando `auto-jobs search` / `auto-jobs run`.

### Modos de operação (`config.yaml` → `application`)

| Config | Comportamento |
|---|---|
| `mode: review` | Gera currículo/carta adaptados mas não abre navegador nem envia nada |
| `mode: auto`, `dry_run: true` | Abre o formulário real e preenche tudo, mas **não clica em enviar** |
| `mode: auto`, `dry_run: false` | Preenche e **envia de fato** a candidatura |

## Descobrindo os tokens das empresas

- **Greenhouse**: acesse a página de vagas da empresa
  (`https://boards.greenhouse.io/<token>`) — `<token>` é o que vai em
  `companies.greenhouse` no config.
- **Lever**: acesse `https://jobs.lever.co/<token>` — mesma lógica.

## Testes

```bash
pytest
```

## Estrutura

```
auto-jobs/
  config.example.yaml       # copie para config.yaml
  data/
    resume_base.yaml        # seu currículo estruturado (edite com dados reais)
    generated/               # docx gerados (gitignored)
    applications.db          # tracker sqlite (gitignored)
  src/auto_jobs/
    cli.py                   # comandos search / run
    config.py
    models.py
    tracker.py
    sources/                 # greenhouse.py, lever.py (busca de vagas)
    resume/                  # parser.py, tailor.py, render.py
    apply/                   # greenhouse_apply.py, lever_apply.py (Playwright)
  tests/
```
