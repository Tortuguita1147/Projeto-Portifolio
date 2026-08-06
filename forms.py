# -*- coding: utf-8 -*-
"""
Formulários WTForms — trazem validação de dados E proteção CSRF embutida
(Flask-WTF injeta token CSRF em todo formulário e valida no submit).

Nenhuma rota POST da aplicação aceita dados sem token CSRF válido.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    DateField,
    MultipleFileField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional

# Categorias fixas do painel — a fotógrafa escolhe uma (ou "Outro").
CATEGORIAS = [
    ("casamento", "Casamento"),
    ("ensaio", "Ensaio"),
    ("gestante", "Gestante"),
    ("aniversario", "Aniversário"),
    ("15anos", "15 anos"),
    ("familia", "Família"),
    ("evento", "Evento / Festa"),
    ("outro", "Outro"),
]

# Upload aceita apenas imagens — a validação dupla (extensão + Pillow)
# acontece no storage.py; aqui filtramos pelo mimetype via FileAllowed.
FOTOS_ALLOWED = FileAllowed(
    {"jpg", "jpeg", "png", "webp"}, "Apenas imagens JPG, PNG ou WebP."
)


class LoginForm(FlaskForm):
    senha = PasswordField("Senha", validators=[DataRequired()])
    entrar = SubmitField("Entrar no painel")


class EventoForm(FlaskForm):
    nome_cliente = StringField(
        "Nome do cliente", validators=[DataRequired(), Length(max=120)]
    )
    categoria = SelectField(
        "Categoria", choices=CATEGORIAS, validators=[DataRequired()]
    )
    data_evento = DateField(
        "Data do evento", validators=[DataRequired()], format="%Y-%m-%d",
        render_kw={"type": "date", "required": True},
    )
    observacoes = TextAreaField(
        "Observações internas (nunca aparecem para o cliente)",
        validators=[Optional(), Length(max=2000)],
    )
    expira_em = DateField(
        "Expira em (opcional — deixe vazio para não expirar)",
        validators=[Optional()], format="%Y-%m-%d",
        render_kw={"type": "date"},
    )
    salvar = SubmitField("Salvar evento e gerar código de acesso")


class UploadFotosForm(FlaskForm):
    fotos = MultipleFileField(
        "Fotos (pode selecionar várias)", validators=[DataRequired(), FOTOS_ALLOWED]
    )
    enviar = SubmitField("Enviar fotos")


class AcessoForm(FlaskForm):
    """Formulário público da home: 'Já é cliente? Acesse sua galeria'."""
    codigo = StringField(
        "Código de acesso",
        validators=[DataRequired(), Length(min=10, max=60)],
        render_kw={
            "placeholder": "Seu código de acesso",
            "autocomplete": "off",
            "maxlength": "60",
            "required": True,
        },
    )
    entrar = SubmitField("Acessar galeria")
