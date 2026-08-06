# -*- coding: utf-8 -*-
"""
Rotas públicas do cliente (galeria privada por código).

SEGURANÇA — decisões por quê:
1. Nunca revelamos o MOTIVO de um acesso falhar: código inexistente, evento
   revogado ou expirado produzem exatamente a mesma resposta (404 genérico
   na URL direta; mensagem genérica no formulário da home). Isso impede
   varredura por tentativa e erro ("esse código existe mas está expirado").
2. A consulta é feita SEMPRE pelo hash SHA-256 do código informado
   (hash_codigo) — o banco nunca recebe o código em claro em texto plano
   pesquisável e o código em si não é comparado contra nada armazenado.
3. Rate limiting (Flask-Limiter) no endpoint de validação do formulário:
   poucas tentativas por minuto por IP, para inviabilizar automação.
4. Cada visita válida é registrada em AcessoLog (data/hora + IP) para a
   fotógrafa acompanhar quando o cliente visualizou.
"""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import content
from access_codes import hash_codigo
from extensions import db, limiter
from forms import AcessoForm
from models import AcessoLog, Evento


cliente_bp = Blueprint("cliente", __name__)


def _buscar_evento_por_codigo(codigo):
    """Evento ativo cujo hash do código informado bate — ou None.

    Um único caminho de falha: None vira 404 genérico, nunca uma pista.
    """
    if not codigo:
        return None
    codigo_hash = hash_codigo(codigo)  # comparamos hashes, nunca texto claro
    evento = Evento.query.filter_by(codigo_hash=codigo_hash).first()
    if evento is None or not evento.ativo_para_acesso:
        return None
    return evento


@cliente_bp.route("/galeria/<codigo>")
def galeria(codigo):
    evento = _buscar_evento_por_codigo(codigo)
    if evento is None:
        # Mesma resposta para código inválido, expirado ou revogado.
        abort(404)

    # Registra a visualização (quando + IP) para a fotógrafa.
    db.session.add(AcessoLog(evento_id=evento.id, ip=request.remote_addr))
    db.session.commit()

    fotos = [
        {
            "url": url_for(
                "static", filename="uploads/" + foto.caminho_thumbnail
            ),
        }
        for foto in sorted(evento.fotos, key=lambda f: f.ordem)
    ]
    return render_template(
        "cliente/galeria.html",
        site=content.SITE,
        evento=evento,
        fotos=fotos,
    )


@cliente_bp.route("/acesso", methods=["POST"])
@limiter.limit("8 per minute")  # trava automação de tentativas por IP
def acesso():
    form = AcessoForm()
    if form.validate_on_submit():
        codigo = form.codigo.data.strip()
        if _buscar_evento_por_codigo(codigo) is not None:
            return redirect(url_for("cliente.galeria", codigo=codigo))
    # Falha genérica — idêntica para código inválido / expirado / revogado.
    flash("Código inválido ou galeria indisponível.", "erro")
    return redirect(url_for("home"))
