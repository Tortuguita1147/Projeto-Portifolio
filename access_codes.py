# -*- coding: utf-8 -*-
"""
Geração e validação de códigos de acesso das galerias privadas.

SEGURANÇA — decisões por quê:
1. `secrets` (não `random`): é criptograficamente seguro — imprevisível até
   para quem conhece a seed/estado. `random` é determinístico e previsível,
   nunca deve ser usado para credenciais.
2. Alfabeto URL-safe de 64 símbolos (A-Z a-z 0-9 - _): 30 caracteres × 6
   bits = ~180 bits de entropia; e nenhum caractere exige percent-encoding
   nem quebra links copiados (sem "/", "?", "#", espaço, acentos).
3. Banco guarda apenas SHA-256 do código: se o banco vazar, o atacante não
   consegue reverter o hash (é função de mão única) nem usar o código.
4. `hmac.compare_digest` para comparação: executa em tempo constante,
   evitando ataques de timing que "adivinham" o hash caractere a caractere.
5. Caso o código se perca, ele NÃO é recuperável (nem pela fotógrafa):
   a saída é gerar um novo código (revoga o antigo automaticamente).
"""

import hashlib
import hmac
import secrets

ALFABETO = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    "-_"
)

COMPRIMENTO = 30


def gerar_codigo(comprimento: int = COMPRIMENTO) -> str:
    """Gera um código de acesso único, criptograficamente seguro."""
    return "".join(secrets.choice(ALFABETO) for _ in range(comprimento))


def hash_codigo(codigo: str) -> str:
    """SHA-256 hex do código — é ISSO que vai para o banco."""
    return hashlib.sha256(codigo.encode("utf-8")).hexdigest()


def verificar_codigo(codigo: str, codigo_hash: str) -> bool:
    """Compara o código informado com o hash salvo (tempo constante)."""
    if not codigo or not codigo_hash:
        return False
    return hmac.compare_digest(hash_codigo(codigo), codigo_hash)
