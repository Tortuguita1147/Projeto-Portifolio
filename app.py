# -*- coding: utf-8 -*-
"""
Rayane Yasmin Fotografia — site institucional (Flask).

Otimizações aplicadas:
- Flask-Compress: comprime HTML/CSS/JS/JSON com gzip.
- Cache de estáticos por 1 ano (SEND_FILE_MAX_AGE_DEFAULT).
- Whitenoise (produção): serve /static/ de forma eficiente sem Nginx.
- Cabeçalhos de segurança leves em toda resposta.

Galerias privadas por código de acesso:
- /admin/*  → painel da fotógrafa (login, eventos, upload).
- /galeria/<codigo> e /acesso → acesso do cliente.
- Banco PostgreSQL (Render) ou SQLite (dev local).

Para deploy no Render.com: siga as instruções no README.md.
"""

import os
from pathlib import Path

from flask import Flask, render_template, request
from flask_login import login_manager as _lm  # noqa: F401  (registro abaixo)
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash

import content
from blueprints.admin import admin_bp, registrar_comando_admin
from blueprints.cliente import cliente_bp
from config import Config
from extensions import db, limiter, login_manager
from forms import AcessoForm
from models import AdminUser
from storage import StorageLocal

# Proteção CSRF global.
csrf = CSRFProtect()

# --- Compressão gzip -------------------------------------------------------
try:
    from flask_compress import Compress
    HAS_COMPRESS = True
except ImportError:
    HAS_COMPRESS = False

# --- Whitenoise: serve /static/ em produção sem Nginx ----------------------
try:
    from whitenoise import WhiteNoise
    HAS_WHITENOISE = True
except ImportError:
    HAS_WHITENOISE = False


@login_manager.user_loader
def carregar_usuario(user_id):
    """Flask-Login: a única conta do painel é a da fotógrafa (id fixo)."""
    if user_id == "admin":
        return AdminUser()
    return None


def _inicializar_storage(app):
    """Cria a camada de armazenamento com as raízes reais de disco."""
    upload_root = Path(app.config["UPLOAD_ROOT"])
    if not upload_root.is_absolute():
        upload_root = Path(app.root_path) / upload_root

    originais_root = Path(app.config["ORIGINAIS_ROOT"])
    if not originais_root.is_absolute():
        originais_root = Path(app.root_path) / originais_root

    storage = StorageLocal(upload_root, originais_root)
    app.extensions["storage"] = storage
    return storage


def render_home(erro_acesso=None, status=200):
    """Renderiza a home one-page — usada pela rota "/", pelo erro 429 e
    por qualquer outro ponto que precise reexibir a página (form de acesso)."""
    return (
        render_template(
            "index.html",
            site=content.SITE,
            hero=content.HERO,
            sobre=content.SOBRE,
            especialidades=content.ESPECIALIDADES,
            galeria=content.GALERIA,
            diferenciais=content.DIFERENCIAIS,
            processo=content.PROCESSO,
            depoimentos=content.DEPOIMENTOS,
            pacotes=content.PACOTES,
            faq=content.FAQ,
            # Instância real para renderizar o token CSRF no form público
            form_acesso=AcessoForm(),
            erro_acesso=erro_acesso,
        ),
        status,
    )


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ----- senha do admin: só hash vindo de ambiente (nunca no código) -----
    # 1) ADMIN_PASSWORD_HASH (recomendado) → usado direto.
    # 2) ADMIN_PASSWORD (conveniência dev)  → hasheada em memória no boot.
    # 3) nenhuma das duas → painel inacessível com aviso claro.
    if not app.config.get("ADMIN_PASSWORD_HASH"):
        if app.config.get("ADMIN_PASSWORD"):
            app.config["ADMIN_PASSWORD_HASH"] = generate_password_hash(
                app.config["ADMIN_PASSWORD"]
            )
            print("[aviso] ADMIN_PASSWORD_HASH não definida; usando ADMIN_PASSWORD "
                  "hasheada em memória (apenas para desenvolvimento).")
        else:
            print("[aviso] ADMIN_PASSWORD_HASH não definida. O painel /admin não "
                  "aceitará login. Gere o hash com: "
                  "flask --app app admin-password 'sua-senha'")

    # ----- extensões -----
    db.init_app(app)
    Migrate(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Faça login para acessar o painel."
    login_manager.login_message_category = "aviso"
    limiter.init_app(app)

    _inicializar_storage(app)
    registrar_comando_admin(app)

    # ----- Whitenoise (produção sem Nginx) -----
    if HAS_WHITENOISE:
        static_root = os.path.join(app.root_path, "static")
        # max_age diretamente no construtor para servir /static/ com cache de 1 ano
        app.wsgi_app = WhiteNoise(
            app.wsgi_app,
            root=static_root,
            prefix="static/",
            max_age=31536000,
        )

    # ----- otimizações -----
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000
    app.config["TEMPLATES_AUTO_RELOAD"] = app.debug

    if HAS_COMPRESS:
        app.config["COMPRESS_MIMETYPES"] = [
            "text/html",
            "text/css",
            "text/xml",
            "application/json",
            "application/javascript",
            "image/svg+xml",
        ]
        app.config["COMPRESS_LEVEL"] = 6
        app.config["COMPRESS_MIN_SIZE"] = 500
        Compress(app)

    # ----- rotas -----
    app.register_blueprint(admin_bp)
    app.register_blueprint(cliente_bp)

    @app.route("/")
    def home():
        return render_home()

    # ----- erros: respostas genéricas (nunca revelam motivos internos) -----
    @app.errorhandler(404)
    def pagina_nao_encontrada(e):
        return render_template("404.html", site=content.SITE), 404

    @app.errorhandler(429)
    def muitas_tentativas(e):
        # Rate limiter estourado (formulário de acesso, login): mensagem
        # igualmente genérica, sem detalhes.
        return render_home(
            erro_acesso="Muitas tentativas. Aguarde alguns minutos e tente novamente.",
            status=429,
        )

    # ----- cabeçalhos de segurança -----
    @app.after_request
    def add_security_and_cache_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        # HSTS (força HTTPS no navegador por 1 ano) — Render já faz SSL,
        # mas este header é segurança extra.
        if not app.debug and request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains"
            )
        return response

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
