"""Ponto de entrada: lê uma proposta em PDF e atualiza um modelo .docx."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from extractor import extrair_proposta
from updater import atualizar_documento


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sincroniza uma proposta comercial (PDF) em um documento modelo (.docx)."
    )
    parser.add_argument("pdf", help="Caminho para a proposta em PDF")
    parser.add_argument("modelo", help="Caminho para o documento modelo .docx")
    parser.add_argument(
        "-o",
        "--saida",
        default="documento_atualizado.docx",
        help="Caminho do documento atualizado (default: documento_atualizado.docx)",
    )
    args = parser.parse_args()

    proposta = extrair_proposta(args.pdf)
    print("Dados extraídos da proposta:")
    print(json.dumps(proposta.to_dict(), indent=2, ensure_ascii=False))

    saida = atualizar_documento(args.modelo, args.saida, proposta)
    print(f"\nDocumento atualizado salvo em: {saida}")


if __name__ == "__main__":
    main()
