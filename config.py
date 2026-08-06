# -*- coding: utf-8 -*-
"""
Configuração da aplicação — carregada de variáveis de ambiente.

Regra de segurança: NUNCA coloque senha, secret key ou tokens no
código-fonte. Tudo que é sensível vem de variáveis de ambiente
(ver README.md — seção "Variáveis de ambiente").
"""

import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # Chave usada para assinar a sessão e os tokens CSRF.
    # Em produção, defina uma chave longa e aleatória:
    #   python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-troque-esta-chave-em-producao")

    # Hash da senha do ADMIN (werkzeug.security.generate_password_hash).
    # O código de acesso de cada evento fica hasheado no banco separadamente.
    # Gere com:  flask --app app admin-password "sua-senha"
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")
    # Alternativa de desenvolvimento: senha em texto puro (nunca em produção).
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

    # --- Banco de dados ---
    # Render define DATABASE_URL automaticamente ao provisionar PostgreSQL.
    # A string pode vir como "postgres://" mas SQLAlchemy exige "postgresql://".
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///site.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Uploads ---
    # No Render com Disk, as pastas ficam no disco persistente.
    # O render.yaml monta o disco em /opt/render/project/src/data.
    # Se RENDER_DISK_PATH existir (definido pelo Render), usa ele.
    # Caso contrário, usa pastas locais (somem ao redeployar).
    _disk = os.environ.get("RENDER_DISK_PATH", "")
    if _disk:
        UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", os.path.join(_disk, "uploads"))
        ORIGINAIS_ROOT = os.environ.get("ORIGINAIS_ROOT", os.path.join(_disk, "originais"))
    else:
        UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", "static/uploads")
        ORIGINAIS_ROOT = os.environ.get("ORIGINAIS_ROOT", "instance/uploads/originais")

    THUMB_MAX = (1600, 1600)
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 50 * 1024 * 1024))

    # --- Rate limiter ---
    # Em produção com múltiplos workers gunicorn, "memory://" NÃO funciona
    # (cada worker tem sua própria memória). Use Redis.
    # Render Redis: https://render.com/docs/redis
    # Grátis: Redis Cloud (https://redis.com/try-free) — 30 MB, sem cartão.
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200 per hour")
