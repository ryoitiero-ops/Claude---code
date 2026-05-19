"""Interface web para sincronizar proposta (PDF) em um documento modelo (.docx)."""

from __future__ import annotations

import secrets
import tempfile
from pathlib import Path

import mammoth
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from extractor import extrair_proposta
from updater import atualizar_documento


BASE_TMP = Path(tempfile.gettempdir()) / "proposta_sync"
BASE_TMP.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB


def _salvar_upload(arquivo, destino: Path) -> Path:
    nome_seguro = secure_filename(arquivo.filename or "")
    if not nome_seguro:
        abort(400, "Arquivo sem nome válido.")
    caminho = destino / nome_seguro
    arquivo.save(caminho)
    return caminho


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/processar", methods=["POST"])
def processar():
    pdf = request.files.get("pdf")
    modelo = request.files.get("modelo")
    if not pdf or not modelo or not pdf.filename or not modelo.filename:
        flash("Envie tanto o PDF da proposta quanto o documento modelo (.docx).")
        return redirect(url_for("index"))
    if not pdf.filename.lower().endswith(".pdf"):
        flash("O primeiro arquivo precisa ser um PDF.")
        return redirect(url_for("index"))
    if not modelo.filename.lower().endswith(".docx"):
        flash("O modelo precisa ser um arquivo .docx.")
        return redirect(url_for("index"))

    sessao_id = secrets.token_urlsafe(8)
    pasta = BASE_TMP / sessao_id
    pasta.mkdir()

    pdf_path = _salvar_upload(pdf, pasta)
    modelo_path = _salvar_upload(modelo, pasta)
    saida_path = pasta / "documento_atualizado.docx"

    proposta = extrair_proposta(pdf_path)
    atualizar_documento(modelo_path, saida_path, proposta)

    return render_template(
        "resultado.html",
        sessao_id=sessao_id,
        proposta=proposta.to_dict(),
    )


@app.route("/preview/<sessao_id>")
def preview(sessao_id: str):
    arquivo = BASE_TMP / sessao_id / "documento_atualizado.docx"
    if not arquivo.exists():
        abort(404)
    with arquivo.open("rb") as docx:
        html = mammoth.convert_to_html(docx).value
    return render_template("preview.html", conteudo_html=html)


@app.route("/download/<sessao_id>")
def download(sessao_id: str):
    pasta = BASE_TMP / sessao_id
    if not (pasta / "documento_atualizado.docx").exists():
        abort(404)
    return send_from_directory(
        pasta, "documento_atualizado.docx", as_attachment=True
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
