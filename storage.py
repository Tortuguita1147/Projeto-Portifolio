# -*- coding: utf-8 -*-
"""
Camada de armazenamento de fotos — desacoplada das rotas.

Hoje: sistema de arquivos local.
- Thumbnails (resolução web) → pasta PÚBLICA (static/uploads/...) — é o que
  o navegador do cliente carrega.
- Originais → pasta PRIVADA (instance/uploads/originais/...) — fora do
  /static, não acessível pela web; reservados para um futuro "download
  explícito" (rota autenticada por código) e nunca expostos agora.

Amanhã: trocar para S3/Cloudinary implementando a mesma interface
(`salvar_foto`, `remover_foto`, `remover_evento`) com um StorageS3 — nenhuma
rota ou template precisa mudar.

SEGURANÇA — decisões por quê:
1. `secure_filename`: remove qualquer "..", barra ou caractere perigoso do
   nome enviado — mata path traversal (ex.: "../../etc/passwd").
2. O nome final NÃO vem do usuário: geramos um hex aleatório de 128 bits
   (`secrets.token_hex(8)` = 64 bits… 16 hex chars) e mantemos só a
   extensão validada. Nome opaco → URLs impossíveis de adivinhar (ninguém
   "descobre" que um evento existe varrendo caminhos).
3. Allowlist de extensão E mimetype; e o Pillow ainda abre a imagem de
   verdade (`verify()`) — o mimetype informado pelo navegador pode mentir.
4. Thumbnail sempre re-encodado como JPEG RGB (sem metadados executáveis,
   sem SVG/HTML disfarçado) → o servido ao cliente é sempre uma imagem
   sanitizada, nunca o upload bruto.
"""

import secrets
import shutil
from pathlib import Path

from PIL import Image
from werkzeug.utils import secure_filename

EXTENSOES_PERMITIDAS = {"jpg", "jpeg", "png", "webp"}
MIMETYPES_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}


class StorageLocal:
    def __init__(self, upload_root: Path, originais_root: Path):
        # upload_root: pasta pública de thumbnails (ex.: static/uploads)
        # originais_root: pasta privada dos arquivos originais
        self.upload_root = Path(upload_root)
        self.originais_root = Path(originais_root)
        self.thumb_max = (1600, 1600)  # largura/altura máxima exibida na web

    # ---------------------------------------------------------------- utils
    def _dirs(self, evento_id):
        thumbs = self.upload_root / "eventos" / str(evento_id) / "thumbs"
        originais = self.originais_root / "eventos" / str(evento_id) / "originais"
        thumbs.mkdir(parents=True, exist_ok=True)
        originais.mkdir(parents=True, exist_ok=True)
        return thumbs, originais

    # ----------------------------------------------------------------- save
    def salvar_foto(self, evento_id, arquivo):
        """Valida, salva o original (privado) e gera o thumbnail (público).

        Retorna (caminho_original_relativo, caminho_thumbnail_relativo).
        Levanta ValueError para arquivos inválidos — as rotas tratam.
        """
        nome = secure_filename(arquivo.filename or "")
        if not nome:
            raise ValueError("Arquivo sem nome válido.")

        if "." not in nome:
            raise ValueError("Arquivo sem extensão.")
        ext = nome.rsplit(".", 1)[-1].lower()
        if ext not in EXTENSOES_PERMITIDAS:
            raise ValueError(
                f"Extensão .{ext} não permitida (use JPG, PNG ou WebP)."
            )

        if arquivo.mimetype not in MIMETYPES_PERMITIDOS:
            raise ValueError("Tipo de arquivo não permitido.")

        thumbs_dir, originais_dir = self._dirs(evento_id)

        # Nome opaco no disco: o nome do usuário nunca é usado (colisões e
        # adivinhação de URL ficam impossíveis).
        token = secrets.token_hex(16)
        nome_original = f"{token}.{ext}"
        caminho_original = originais_dir / nome_original

        arquivo.save(str(caminho_original))

        # Validação de verdade: abre a imagem (mimetype informado pode ser
        # falso) e gera o thumbnail em resolução web.
        try:
            with Image.open(caminho_original) as img:
                img.verify()  # garante que é uma imagem válida e completa
            with Image.open(caminho_original) as img:
                # Re-encode para JPEG RGB → formato único, sem alpha problemático
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGBA")
                    fundo = Image.new("RGB", img.size, (255, 255, 255))
                    fundo.paste(img, mask=img.split()[-1])
                    img = fundo
                else:
                    img = img.convert("RGB")
                img.thumbnail(self.thumb_max, Image.LANCZOS)
                nome_thumb = f"{token}_thumb.jpg"
                caminho_thumb = thumbs_dir / nome_thumb
                img.save(str(caminho_thumb), "JPEG", quality=85, optimize=True)
        except Exception:
            # imagem corrompida/não-imagem: remove o que foi salvo e rejeita
            caminho_original.unlink(missing_ok=True)
            raise ValueError("Arquivo corrompido ou não é uma imagem válida.")

        return (
            f"eventos/{evento_id}/originais/{nome_original}",   # rel. ORIGINAIS_ROOT
            f"eventos/{evento_id}/thumbs/{nome_thumb}",          # rel. UPLOAD_ROOT
        )

    # -------------------------------------------------------------- remove
    def remover_foto(self, rel_original, rel_thumb):
        """Remove os dois arquivos (se existirem). Não falha se sumiram."""
        for root, rel in ((self.originais_root, rel_original),
                          (self.upload_root, rel_thumb)):
            if rel:
                try:
                    (root / rel).unlink(missing_ok=True)
                except OSError:
                    pass

    def remover_evento(self, evento_id):
        """Remove a pasta inteira do evento (originais + thumbs)."""
        shutil.rmtree(self.upload_root / "eventos" / str(evento_id), ignore_errors=True)
        shutil.rmtree(self.originais_root / "eventos" / str(evento_id), ignore_errors=True)


# instância global; app.py injeta as raízes reais na inicialização
storage = StorageLocal(Path("static/uploads"), Path("instance/uploads/originais"))
