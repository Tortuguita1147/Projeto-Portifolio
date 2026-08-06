# -*- coding: utf-8 -*-
"""
Teste de fluxo completo (usa banco e pastas temporárias, não toca no seu
ambiente de desenvolvimento):

    login do painel → criar evento → gerar código (única vez) → upload de
    fotos → acesso do cliente pelo link → código errado/expirado dão o
    mesmo 404 genérico.

Rode com:  python -m unittest tests.test_fluxo -v
"""

import io
import os
import shutil
import tempfile
import unittest

# Banco e pastas 100% temporários ANTES de importar a app
_TMP = tempfile.mkdtemp(prefix="rayane_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TMP, 'teste.db')}"
os.environ["UPLOAD_ROOT"] = os.path.join(_TMP, "uploads")
os.environ["ORIGINAIS_ROOT"] = os.path.join(_TMP, "originais")
os.environ["SECRET_KEY"] = "chave-de-teste"

from werkzeug.security import generate_password_hash

os.environ["ADMIN_PASSWORD_HASH"] = generate_password_hash("senha-teste")

from PIL import Image

from app import app
from extensions import db


def _imagem_jpeg(nome="foto_teste.jpg"):
    buf = io.BytesIO()
    Image.new("RGB", (200, 150), (120, 80, 200)).save(buf, "JPEG")
    buf.seek(0)
    return buf, nome


class TestFluxo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,  # teste sem token CSRF (em dev/prod fica ligado)
            RATELIMIT_ENABLED=False,
        )
        with app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        shutil.rmtree(_TMP, ignore_errors=True)

    def setUp(self):
        self.client = app.test_client()

    def _login_admin(self):
        return self.client.post(
            "/admin/login", data={"senha": "senha-teste"}, follow_redirects=True
        )

    def _criar_evento(self):
        return self.client.post(
            "/admin/eventos/novo",
            data={
                "nome_cliente": "Ana & João",
                "categoria": "casamento",
                "data_evento": "2025-01-15",
                "observacoes": "obs interna",
            },
            follow_redirects=False,
        )

    # ---------------------------------------------------------------- testes
    def test_home_publica_funciona(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Já é cliente?", resp.get_data(as_text=True))

    def test_admin_exige_login(self):
        resp = self.client.get("/admin/")
        # redireciona para o login (307/302) quando deslogado
        self.assertIn(resp.status_code, (301, 302, 307))

    def test_login_senha_errada(self):
        resp = self.client.post(
            "/admin/login", data={"senha": "errada"}, follow_redirects=True
        )
        self.assertIn("Senha incorreta", resp.get_data(as_text=True))

    def test_fluxo_completo(self):
        # 1) login
        resp = self._login_admin()
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Eventos e galerias", resp.get_data(as_text=True))

        # 2) criar evento → redireciona para a tela do código
        resp = self._criar_evento()
        self.assertIn(resp.status_code, (301, 302, 307))
        with app.app_context():
            from models import Evento

            evento = Evento.query.first()
            self.assertIsNotNone(evento)
            # hash salvo nunca é o código em claro (64 hex chars)
            self.assertEqual(len(evento.codigo_hash), 64)
            evento_id = evento.id

        # 3) tela do código (uma única vez)
        resp = self.client.get(f"/admin/eventos/{evento_id}/codigo")
        pagina = resp.get_data(as_text=True)
        self.assertIn("Guarde este código", pagina)

        # extrai o código exibido (bloco data-codigo — atributo sem valor)
        import re
        m = re.search(r'data-codigo>([^<]+)</div>', pagina)
        self.assertIsNotNone(m, "código não encontrado na página")
        codigo = m.group(1).strip()
        self.assertEqual(len(codigo), 30)

        # 4) segunda visita → código NÃO aparece de novo
        resp = self.client.get(f"/admin/eventos/{evento_id}/codigo", follow_redirects=True)
        self.assertNotIn(codigo, resp.get_data(as_text=True))

        # 5) upload de fotos
        buf, nome = _imagem_jpeg()
        resp = self.client.post(
            f"/admin/eventos/{evento_id}/fotos",
            data={"fotos": (buf, nome)},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertIn("foto(s) enviada(s)", resp.get_data(as_text=True))
        with app.app_context():
            from models import Foto

            foto = Foto.query.first()
            self.assertIsNotNone(foto)
            self.assertTrue(foto.caminho_thumbnail.endswith("_thumb.jpg"))
            # original fica fora da pasta pública
            caminho_original = os.path.join(_TMP, "originais", foto.caminho_arquivo)
            self.assertTrue(os.path.exists(caminho_original))

        # 6) upload rejeita arquivo que não é imagem
        resp = self.client.post(
            f"/admin/eventos/{evento_id}/fotos",
            data={"fotos": (io.BytesIO(b"<html>nao e imagem</html>"), "fake.html")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertNotIn("enviada(s) com sucesso", resp.get_data(as_text=True))

        # 7) cliente acessa pelo código → 200 e mostra o evento
        resp = self.client.get(f"/galeria/{codigo}")
        self.assertEqual(resp.status_code, 200)
        pagina = resp.get_data(as_text=True)
        self.assertIn("Ana &amp; João", pagina)  # HTML escapa o & 
        self.assertIn("casamento", pagina)

        # 8) código errado → 404 genérico (sem pista do motivo)
        resp = self.client.get("/galeria/codigo-totalmente-errado")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Página não encontrada", resp.get_data(as_text=True))

        # 9) formulário público da home com código errado → mensagem genérica
        resp = self.client.post(
            "/acesso", data={"codigo": "codigo-totalmente-errado"}, follow_redirects=True
        )
        self.assertIn("Código inválido ou galeria indisponível", resp.get_data(as_text=True))

        # 10) revogar → mesmo código passa a dar 404
        with app.app_context():
            evento = Evento.query.get(evento_id)
            evento.status = "revogado"
            db.session.commit()
        resp = self.client.get(f"/galeria/{codigo}")
        self.assertEqual(resp.status_code, 404)

    def test_upload_arquivo_nao_imagem(self):
        # sem login → bloqueado
        resp = self.client.post(
            "/admin/eventos/1/fotos",
            data={"fotos": (io.BytesIO(b"x"), "fake.jpg")},
            content_type="multipart/form-data",
        )
        self.assertIn(resp.status_code, (301, 302, 307))


if __name__ == "__main__":
    unittest.main()
