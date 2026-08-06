# -*- coding: utf-8 -*-
"""
Singletons das extensões Flask — isolados aqui para evitar import circular
entre app.py, blueprints e models.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

login_manager = LoginManager()

# Rate limiter: a chave padrão é o IP do cliente (get_remote_address).
limiter = Limiter(key_func=get_remote_address)
