# -*- coding: utf-8 -*-
"""
Testes unitários — geração/validação de código de acesso e lógica de
status do Evento (sem precisar de banco de dados).

Rode com:  python -m unittest tests.test_access_codes -v
"""

import re
import unittest
from datetime import date, timedelta

from access_codes import ALFABETO, COMPRIMENTO, gerar_codigo, hash_codigo, verificar_codigo
from models import Evento

PADRAO_URLSAFE = re.compile(r"^[A-Za-z0-9_-]+$")


class TestGerarCodigo(unittest.TestCase):
    def test_comprimento(self):
        for _ in range(50):
            self.assertEqual(len(gerar_codigo()), COMPRIMENTO)

    def test_alfabeto_urlsafe(self):
        # Só letras, números, "-" e "_" — nada que quebre URL ou exija encoding
        for _ in range(50):
            codigo = gerar_codigo()
            self.assertRegex(codigo, PADRAO_URLSAFE)
            for char in codigo:
                self.assertIn(char, ALFABETO)

    def test_unicidade(self):
        # 500 códigos sem repetição (colisão seria ~impossível com 180 bits)
        codigos = {gerar_codigo() for _ in range(500)}
        self.assertEqual(len(codigos), 500)

    def test_diferentes_entre_si(self):
        self.assertNotEqual(gerar_codigo(), gerar_codigo())


class TestHashCodigo(unittest.TestCase):
    def test_hash_sha256_hex(self):
        h = hash_codigo("AbC123-_xyz")
        self.assertEqual(len(h), 64)
        self.assertRegex(h, r"^[0-9a-f]{64}$")

    def test_deterministico(self):
        self.assertEqual(hash_codigo("codigo"), hash_codigo("codigo"))

    def test_sensivel_a_maiusculas(self):
        # Códigos diferenciam maiúsculas/minúsculas de propósito
        self.assertNotEqual(hash_codigo("AbC"), hash_codigo("abc"))


class TestVerificarCodigo(unittest.TestCase):
    def test_codigo_correto(self):
        codigo = gerar_codigo()
        self.assertTrue(verificar_codigo(codigo, hash_codigo(codigo)))

    def test_codigo_errado(self):
        codigo = gerar_codigo()
        self.assertFalse(verificar_codigo("outro-codigo", hash_codigo(codigo)))

    def test_entradas_vazias(self):
        self.assertFalse(verificar_codigo("", hash_codigo("x")))
        self.assertFalse(verificar_codigo("x", ""))
        self.assertFalse(verificar_codigo("", ""))


class TestStatusEvento(unittest.TestCase):
    """Lógica de status derivado ('expirado') sem tocar no banco."""

    def _evento(self, status="ativo", expira_em=None):
        return Evento(
            nome_cliente="Cliente Teste",
            categoria="ensaio",
            data_evento=date.today(),
            codigo_hash="a" * 64,
            status=status,
            expira_em=expira_em,
        )

    def test_ativo_sem_expiracao(self):
        self.assertEqual(self._evento().status_efetivo, "ativo")
        self.assertTrue(self._evento().ativo_para_acesso)

    def test_expirado_pela_data(self):
        ev = self._evento(expira_em=date.today() - timedelta(days=1))
        self.assertEqual(ev.status_efetivo, "expirado")
        self.assertFalse(ev.ativo_para_acesso)

    def test_nao_expirado_no_ultimo_dia(self):
        ev = self._evento(expira_em=date.today())
        self.assertEqual(ev.status_efetivo, "ativo")
        self.assertTrue(ev.ativo_para_acesso)

    def test_revogado_vence_data(self):
        # Mesmo com data futura, revogado bloqueia
        ev = self._evento(status="revogado", expira_em=date.today() + timedelta(days=30))
        self.assertEqual(ev.status_efetivo, "revogado")
        self.assertFalse(ev.ativo_para_acesso)


if __name__ == "__main__":
    unittest.main()
