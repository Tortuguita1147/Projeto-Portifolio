# -*- coding: utf-8 -*-
"""
Modelos do banco de dados (SQLAlchemy / Flask-Migrate).

Três entidades:
- Evento: um ensaio/casamento/evento com galeria privada. Guarda APENAS o
  hash SHA-256 do código de acesso — nunca o código em texto puro.
- Foto: fotos de um evento (original separado do thumbnail).
- AcessoLog: registro de quando/quem acessou a galeria (para a fotógrafa
  saber que o cliente visualizou).

Migrações: os modelos são gerenciados por Alembic (Flask-Migrate):
    flask --app app db migrate -m "descrição"
    flask --app app db upgrade
"""

from datetime import date, datetime

from flask_login import UserMixin

from extensions import db


class AdminUser(UserMixin):
    """Usuário do painel administrativo.

    O site tem UMA fotógrafa — não há tabela de usuários. O login autentica
    a senha definida no ambiente (ADMIN_PASSWORD_HASH) e "loga" este objeto
    fixo via Flask-Login. Senha nunca fica no banco nem no código-fonte.
    """

    id = "admin"


class Evento(db.Model):
    __tablename__ = "evento"

    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(80), nullable=False)
    data_evento = db.Column(db.Date, nullable=False)
    observacoes = db.Column(db.Text, nullable=False, default="")
    # SHA-256 hex do código de acesso (64 chars). Único + indexado.
    codigo_hash = db.Column(db.String(64), unique=True, index=True, nullable=False)
    expira_em = db.Column(db.Date, nullable=True)  # null = não expira
    status = db.Column(db.String(20), nullable=False, default="ativo")  # ativo | revogado
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    fotos = db.relationship(
        "Foto",
        backref="evento",
        cascade="all, delete-orphan",
        order_by="Foto.ordem",
    )
    acessos = db.relationship(
        "AcessoLog",
        backref="evento",
        cascade="all, delete-orphan",
        order_by="AcessoLog.acessado_em.desc()",
    )

    @property
    def status_efetivo(self):
        """Status real: "expirado" é derivado — nunca salvo no banco.

        'revogado' (manual) vence a data de expiração; caso contrário, se
        a data de expiração passou, o evento está 'expirado'.
        """
        if self.status == "revogado":
            return "revogado"
        if self.expira_em and self.expira_em < date.today():
            return "expirado"
        return "ativo"

    @property
    def ativo_para_acesso(self):
        """True se o código pode liberar a galeria hoje."""
        if self.status != "ativo":
            return False
        if self.expira_em and self.expira_em < date.today():
            return False
        return True

    @property
    def ultimo_acesso(self):
        return max((a.acessado_em for a in self.acessos), default=None)

    @property
    def total_fotos(self):
        return len(self.fotos)


class Foto(db.Model):
    __tablename__ = "foto"

    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey("evento.id"), nullable=False)
    # Caminhos RELATIVOS às raízes de cada tipo (ver storage.py):
    #   caminho_arquivo   → relativo a ORIGINAIS_ROOT (privado, fora do static)
    #   caminho_thumbnail → relativo a UPLOAD_ROOT (público, /static/uploads/...)
    caminho_arquivo = db.Column(db.String(255), nullable=False)
    caminho_thumbnail = db.Column(db.String(255), nullable=False)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class AcessoLog(db.Model):
    __tablename__ = "acesso_log"

    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey("evento.id"), nullable=False)
    acessado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip = db.Column(db.String(45), nullable=True)  # IPv4/IPv6
