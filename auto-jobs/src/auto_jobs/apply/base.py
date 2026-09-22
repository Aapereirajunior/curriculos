"""Helpers genéricos de preenchimento de formulário usados pelos automatizadores
específicos de cada ATS (Greenhouse, Lever).

Formulários de candidatura variam bastante entre empresas mesmo dentro do
mesmo ATS (perguntas de triagem customizadas, campos obrigatórios diferentes
etc). Estes helpers tentam casar campos pelo texto do label/placeholder e
são propositalmente tolerantes a falhas — um campo que não é encontrado é
logado como aviso em vez de derrubar a execução inteira, para não perder o
progresso já feito no formulário.
"""

import logging

from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def fill_text_field(page: Page, label_substring: str, value: str) -> bool:
    if not value:
        return False
    try:
        locator = page.get_by_label(label_substring, exact=False)
        if locator.count() == 0:
            return False
        locator.first.fill(value)
        return True
    except Exception as exc:  # noqa: BLE001 - formulários variam muito, seguimos em frente
        logger.warning("Não consegui preencher o campo '%s': %s", label_substring, exc)
        return False


def upload_file_field(page: Page, label_substring: str, file_path: str) -> bool:
    try:
        locator = page.get_by_label(label_substring, exact=False)
        if locator.count() == 0:
            return False
        locator.first.set_input_files(file_path)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Não consegui anexar arquivo no campo '%s': %s", label_substring, exc)
        return False


def answer_default_questions(page: Page, default_answers: dict[str, str]) -> None:
    """Tenta responder perguntas de triagem conhecidas com base em substring do label."""
    for question_substring, answer in default_answers.items():
        filled = fill_text_field(page, question_substring, answer)
        if not filled:
            try:
                radio = page.get_by_label(answer, exact=False)
                if radio.count() > 0:
                    radio.first.check()
            except Exception as exc:  # noqa: BLE001
                logger.debug("Pergunta '%s' não encontrada/respondida: %s", question_substring, exc)
