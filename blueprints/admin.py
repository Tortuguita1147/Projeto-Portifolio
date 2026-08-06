# -*- coding: utf-8 -*-
"""
Área administrativa — uso exclusivo da fotógrafa (login por senha única).

Fluxo de criação de evento:
1. POST /admin/eventos/novo  → valida EventoForm, gera o código de acesso,
   salva APENAS o hash SHA-256 e guarda o código em claro temporariamente
   na sessão (uma única requisição) para ser exibido uma única vez.
2. GET /admin/eventos/<id>/codigo → mostra o código + botão copiar e APAGA
   a sessão: a partir daí o código em claro não existe mais em lugar nenhum.
   Se perder, gera-se um novo (rota regenerar), que revoga o anterior.
"""

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from access_codes import gerar_codigo, hash_codigo
from extensions import db, limiter
from forms import EventoForm, LoginForm, UploadFotosForm
from models import AdminUser, Evento, Foto

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ------------------------------------------------------------------- login
@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")  # trava brute-force no login do painel
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        senha_hash = current_app.config.get("ADMIN_PASSWORD_HASH")
        if senha_hash and check_password_hash(senha_hash, form.senha.data):
            login_user(AdminUser())
            proximo = request.args.get("next")
            return redirect(proximo or url_for("admin.dashboard"))
        # Mensagem genérica: não revela se a senha está configurada ou errada.
        flash("Senha incorreta.", "erro")
    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Você saiu do painel.", "ok")
    return redirect(url_for("admin.login"))


# -------------------------------------------------------------- dashboard
@admin_bp.route("/")
@login_required
def dashboard():
    eventos = Evento.query.order_by(Evento.criado_em.desc()).all()
    return render_template("admin/dashboard.html", eventos=eventos)


# ------------------------------------------------------------- novo evento
@admin_bp.route("/eventos/novo", methods=["GET", "POST"])
@login_required
def evento_novo():
    form = EventoForm()
    if form.validate_on_submit():
        codigo = gerar_codigo()
        evento = Evento(
            nome_cliente=form.nome_cliente.data.strip(),
            categoria=form.categoria.data,
            data_evento=form.data_evento.data,
            observacoes=(form.observacoes.data or "").strip(),
            expira_em=form.expira_em.data,
            codigo_hash=hash_codigo(codigo),  # só o hash vai para o banco
            status="ativo",
        )
        db.session.add(evento)
        db.session.commit()

        # Código em claro viaja apenas dentro da sessão (assinada) e é
        # removido na primeira exibição — nunca persiste no banco.
        session["codigo_unico"] = {"evento_id": evento.id, "codigo": codigo}
        return redirect(url_for("admin.evento_codigo", evento_id=evento.id))

    return render_template("admin/evento_form.html", form=form, evento=None)


# -------------------------------------------------- código (uma única vez)
@admin_bp.route("/eventos/<int:evento_id>/codigo")
@login_required
def evento_codigo(evento_id):
    evento = db.get_or_404(Evento, evento_id)
    info = session.pop("codigo_unico", None)
    if not info or info.get("evento_id") != evento_id:
        # Segunda visita: o código já foi consumido e não é recuperável.
        flash(
            "O código de acesso é exibido apenas uma vez e não pode ser "
            "recuperado. Se precisar, gere um novo código.",
            "aviso",
        )
        return redirect(url_for("admin.evento_detalhe", evento_id=evento.id))
    return render_template(
        "admin/evento_codigo.html", evento=evento, codigo=info["codigo"]
    )


# -------------------------------------------------------- regenerar código
@admin_bp.route("/eventos/<int:evento_id>/codigo/regenerar", methods=["POST"])
@login_required
def evento_codigo_regenerar(evento_id):
    """Gera um NOVO código (o antigo deixa de funcionar) e exibe uma vez."""
    evento = db.get_or_404(Evento, evento_id)
    codigo = gerar_codigo()
    evento.codigo_hash = hash_codigo(codigo)
    db.session.commit()
    session["codigo_unico"] = {"evento_id": evento.id, "codigo": codigo}
    flash("Novo código gerado. O código anterior foi revogado.", "ok")
    return redirect(url_for("admin.evento_codigo", evento_id=evento.id))


# ----------------------------------------------------------- detalhe/editar
@admin_bp.route("/eventos/<int:evento_id>", methods=["GET", "POST"])
@login_required
def evento_detalhe(evento_id):
    evento = db.get_or_404(Evento, evento_id)
    form = EventoForm(obj=evento)
    if form.validate_on_submit():
        evento.nome_cliente = form.nome_cliente.data.strip()
        evento.categoria = form.categoria.data
        evento.data_evento = form.data_evento.data
        evento.observacoes = (form.observacoes.data or "").strip()
        evento.expira_em = form.expira_em.data
        db.session.commit()
        flash("Evento atualizado.", "ok")
        return redirect(url_for("admin.evento_detalhe", evento_id=evento.id))
    upload_form = UploadFotosForm()
    return render_template(
        "admin/evento_detalhe.html", evento=evento, form=form, upload_form=upload_form
    )


# ---------------------------------------------------------------- uploads
@admin_bp.route("/eventos/<int:evento_id>/fotos", methods=["POST"])
@login_required
def evento_fotos(evento_id):
    evento = db.get_or_404(Evento, evento_id)
    form = UploadFotosForm()
    if form.validate_on_submit():
        storage = current_app.extensions["storage"]
        arquivos = [f for f in form.fotos.data if f and f.filename]
        if not arquivos:
            flash("Selecione pelo menos uma foto.", "erro")
            return redirect(url_for("admin.evento_detalhe", evento_id=evento.id))

        salvos, erros = 0, []
        for arquivo in arquivos:
            try:
                rel_original, rel_thumb = storage.salvar_foto(evento.id, arquivo)
            except ValueError as exc:
                erros.append(f"{arquivo.filename}: {exc}")
                continue
            db.session.add(
                Foto(
                    evento_id=evento.id,
                    caminho_arquivo=rel_original,
                    caminho_thumbnail=rel_thumb,
                    ordem=salvos,
                )
            )
            salvos += 1
        db.session.commit()

        # Reordena a sequência final (ordem = posição de envio).
        for i, foto in enumerate(evento.fotos):
            foto.ordem = i
        db.session.commit()

        msg = f"{salvos} foto(s) enviada(s) com sucesso."
        if erros:
            msg += " | Não enviadas: " + "; ".join(erros)
        flash(msg, "ok" if salvos else "erro")
    else:
        flash("Selecione imagens válidas (JPG, PNG ou WebP).", "erro")
    return redirect(url_for("admin.evento_detalhe", evento_id=evento.id))


@admin_bp.route(
    "/eventos/<int:evento_id>/fotos/<int:foto_id>/excluir", methods=["POST"]
)
@login_required
def foto_excluir(evento_id, foto_id):
    foto = db.get_or_404(Foto, foto_id)
    if foto.evento_id != evento_id:
        abort(404)
    storage = current_app.extensions["storage"]
    storage.remover_foto(foto.caminho_arquivo, foto.caminho_thumbnail)
    db.session.delete(foto)
    db.session.commit()
    flash("Foto removida.", "ok")
    return redirect(url_for("admin.evento_detalhe", evento_id=evento.id))


# -------------------------------------------------------- status (revogar)
@admin_bp.route("/eventos/<int:evento_id>/status", methods=["POST"])
@login_required
def evento_status(evento_id):
    evento = db.get_or_404(Evento, evento_id)
    if evento.status == "ativo":
        evento.status = "revogado"
        flash("Código revogado — a galeria não pode mais ser acessada.", "ok")
    else:
        evento.status = "ativo"
        flash("Código reativado.", "ok")
    db.session.commit()
    return redirect(url_for("admin.evento_detalhe", evento_id=evento.id))


# --------------------------------------------------------------- excluir
@admin_bp.route("/eventos/<int:evento_id>/excluir", methods=["POST"])
@login_required
def evento_excluir(evento_id):
    evento = db.get_or_404(Evento, evento_id)
    storage = current_app.extensions["storage"]
    storage.remover_evento(evento.id)
    db.session.delete(evento)  # fotos e logs são apagados em cascata
    db.session.commit()
    flash(f"Evento '{evento.nome_cliente}' excluído.", "ok")
    return redirect(url_for("admin.dashboard"))


# ------------------------------------------------------------------- cli
# Comando para gerar o hash da senha do painel:
#   flask --app app admin-password "minha-senha"
# (o resultado vai na variável de ambiente ADMIN_PASSWORD_HASH)
def registrar_comando_admin(app):
    import click

    @app.cli.command("admin-password")
    @click.argument("senha")
    def admin_password(senha):
        click.echo(generate_password_hash(senha))
