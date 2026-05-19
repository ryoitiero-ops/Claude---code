"""Atualiza um documento .docx substituindo placeholders sem mexer no layout.

A substituição é feita run-a-run (e por parágrafo quando o placeholder está
quebrado entre runs), preservando fonte, tamanho, cor, alinhamento e estilo
originais do documento.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph

from extractor import PropostaComercial


PLACEHOLDER = re.compile(r"\{\{\s*([A-Z_]+)\s*\}\}")


def _mapa_substituicoes(proposta: PropostaComercial) -> dict[str, str]:
    return {
        "CLIENTE": proposta.cliente,
        "EMPRESA": proposta.empresa,
        "CNPJ": proposta.cnpj,
        "SERVICOS": "\n".join(f"• {s}" for s in proposta.servicos),
        "VALOR_TOTAL": proposta.valor_total,
        "DATA_EMISSAO": proposta.data_emissao,
        "DATA_VALIDADE": proposta.data_validade,
        "CONDICOES_PAGAMENTO": proposta.condicoes_pagamento,
        "PRAZO_ENTREGA": proposta.prazo_entrega,
    }


def _substituir_no_paragrafo(paragrafo: Paragraph, mapa: dict[str, str]) -> None:
    texto_completo = paragrafo.text
    if not PLACEHOLDER.search(texto_completo):
        return

    novo_texto = PLACEHOLDER.sub(
        lambda m: mapa.get(m.group(1), m.group(0)) or m.group(0),
        texto_completo,
    )
    if novo_texto == texto_completo:
        return

    # Mantemos o primeiro run com o novo texto e zeramos os demais.
    # Isso preserva a formatação do parágrafo (do primeiro run) sem alterar layout.
    if not paragrafo.runs:
        paragrafo.add_run(novo_texto)
        return

    paragrafo.runs[0].text = novo_texto
    for run in paragrafo.runs[1:]:
        run.text = ""


def atualizar_documento(
    template_path: str | Path,
    saida_path: str | Path,
    proposta: PropostaComercial,
) -> Path:
    """Aplica os dados da proposta em um modelo .docx e salva em saida_path."""
    documento = Document(str(template_path))
    mapa = _mapa_substituicoes(proposta)

    for paragrafo in documento.paragraphs:
        _substituir_no_paragrafo(paragrafo, mapa)

    for tabela in documento.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for paragrafo in celula.paragraphs:
                    _substituir_no_paragrafo(paragrafo, mapa)

    saida = Path(saida_path)
    saida.parent.mkdir(parents=True, exist_ok=True)
    documento.save(str(saida))
    return saida
