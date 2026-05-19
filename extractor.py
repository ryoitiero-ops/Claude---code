"""Extrai dados estruturados de uma proposta comercial em PDF."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

import pdfplumber


@dataclass
class PropostaComercial:
    cliente: str = ""
    empresa: str = ""
    cnpj: str = ""
    servicos: list[str] = field(default_factory=list)
    valor_total: str = ""
    data_emissao: str = ""
    data_validade: str = ""
    condicoes_pagamento: str = ""
    prazo_entrega: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


_CAMPOS = {
    "cliente": r"(?:cliente|contratante)\s*[:\-]\s*(.+)",
    "empresa": r"(?:empresa|raz[ãa]o\s+social)\s*[:\-]\s*(.+)",
    "cnpj": r"cnpj\s*[:\-]\s*([\d./\-]+)",
    "valor_total": r"(?:valor\s+total|total\s+geral)\s*[:\-]\s*(R\$\s*[\d.,]+)",
    "data_emissao": r"(?:data\s+de\s+emiss[ãa]o|emiss[ãa]o)\s*[:\-]\s*(\d{2}/\d{2}/\d{4})",
    "data_validade": r"(?:validade(?:\s+da\s+proposta)?)\s*[:\-]\s*(\d{2}/\d{2}/\d{4})",
    "condicoes_pagamento": r"(?:condi[çc][õo]es\s+de\s+pagamento|pagamento)\s*[:\-]\s*(.+)",
    "prazo_entrega": r"(?:prazo\s+de\s+entrega|entrega)\s*[:\-]\s*(.+)",
}


def _ler_texto_pdf(caminho_pdf: Path) -> str:
    with pdfplumber.open(caminho_pdf) as pdf:
        return "\n".join((pagina.extract_text() or "") for pagina in pdf.pages)


def _extrair_campo(texto: str, padrao: str) -> str:
    match = re.search(padrao, texto, flags=re.IGNORECASE)
    if not match:
        return ""
    return match.group(1).strip().rstrip(".;")


def _extrair_servicos(texto: str) -> list[str]:
    bloco = re.search(
        r"(?:servi[çc]os|produtos|escopo)[^\n]*\n(.+?)(?=\n\s*(?:valor|total|condi|pagamento|prazo)\b)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not bloco:
        return []
    linhas = [linha.strip(" -•\t") for linha in bloco.group(1).splitlines()]
    return [linha for linha in linhas if linha]


def extrair_proposta(caminho_pdf: str | Path) -> PropostaComercial:
    """Lê o PDF e devolve os campos identificados como uma PropostaComercial."""
    texto = _ler_texto_pdf(Path(caminho_pdf))
    proposta = PropostaComercial(
        **{nome: _extrair_campo(texto, padrao) for nome, padrao in _CAMPOS.items()}
    )
    proposta.servicos = _extrair_servicos(texto)
    return proposta
