# Rayane Yasmin Fotografia — site (Flask)

Site institucional one-page feito em Flask + Jinja2, com CSS e JS vanilla
(sem frameworks pesados) — pensado para carregar rápido em qualquer
dispositivo.

**Novidade:** galerias privadas por código de acesso (casamentos, ensaios,
aniversários...). A fotógrafa cria o evento no painel `/admin`, envia as
fotos e recebe um **código único** para repassar ao cliente — só quem tem o
código vê a galeria daquele evento.

## Estrutura do projeto

```
rayane-yasmin-site/
├── app.py                 → fábrica da app: rotas, extensões, compress/cache
├── content.py              → TODO o texto público do site (edite só aqui)
├── config.py               → configuração via variáveis de ambiente
├── extensions.py           → singletons: db, login, rate limiter
├── models.py               → Evento, Foto, AcessoLog (SQLAlchemy)
├── access_codes.py         → geração/validação do código (SHA-256, secrets)
├── storage.py              → salva fotos + gera thumbnail (troca fácil p/ S3)
├── forms.py                → formulários WTForms (login, evento, upload, acesso)
├── blueprints/
│   ├── admin.py            → painel da fotógrafa (/admin/*)
│   └── cliente.py          → acesso do cliente (/galeria/<codigo>, /acesso)
├── requirements.txt
├── Procfile                → comando de start para o Render (gunicorn)
├── render.yaml             → Render Blueprint (web service + PostgreSQL + disk)
├── migrations/             → migrações Alembic (geradas por `flask db migrate`)
├── templates/
│   ├── base.html           → <head>, navegação, rodapé
│   ├── index.html          → home (hero, sobre, galeria, FAQ...) + "Já é cliente?"
│   ├── _modal_galeria.html → modal/lightbox compartilhado (home + galeria privada)
│   ├── 404.html
│   ├── admin/              → login, dashboard, criar/editar evento, código
│   └── cliente/galeria.html→ galeria privada do cliente
└── static/
    ├── css/style.css       → estilos (tokens de cor no topo)
    ├── js/main.js          → menu, FAQ, modal, galeria privada
    ├── images/             → fotos do site público
    └── uploads/            → thumbnails das galerias privadas (gerado em runtime)
```

## Como rodar localmente

```bash
# 1. Ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Variáveis de ambiente (veja a seção abaixo)
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export ADMIN_PASSWORD_HASH="$(flask --app app admin-password 'sua-senha-secreta')"

# 4. Crie o banco (SQLite local + migrações inclusas)
flask --app app db upgrade

# 5. Rode em modo desenvolvimento (recarrega ao salvar arquivos)
flask --app app run --debug

# Acesse em http://127.0.0.1:5000  → painel em http://127.0.0.1:5000/admin
```

> Se preferir, o hash da senha também pode ser gerado com:
> `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('sua-senha'))"`

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `SECRET_KEY` | ✅ produção | Chave que assina sessões e tokens CSRF. Gere com `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_PASSWORD_HASH` | ✅ produção | Hash da senha do painel (`flask --app app admin-password "senha"`). Nunca coloque a senha em texto puro no código |
| `ADMIN_PASSWORD` | só dev | Alternativa de desenvolvimento: senha em texto puro **apenas no ambiente**; a app hasheia em memória no boot |
| `DATABASE_URL` | não | Banco. Padrão: `sqlite:///site.db` (arquivo em `instance/`). Para Postgres: `postgresql://usuario:senha@host:5432/banco` |
| `RATELIMIT_STORAGE_URI` | não | Armazenamento do rate limiter. Padrão: `memory://` (dev). Em produção multi-worker: `redis://localhost:6379` |
| `UPLOAD_ROOT` | não | Pasta pública dos thumbnails. Padrão: `static/uploads` |
| `ORIGINAIS_ROOT` | não | Pasta privada dos originais (fora do `/static`). Padrão: `instance/uploads/originais` |
| `MAX_CONTENT_LENGTH` | não | Tamanho máximo de upload por requisição (bytes). Padrão: 50 MB |

> **Sem `ADMIN_PASSWORD_HASH`/`ADMIN_PASSWORD` o login do painel é recusado**
> com aviso — nunca existe senha padrão "de fábrica".

## Como usar o painel (fluxo da fotógrafa)

1. Acesse `/admin` e faça login com a senha configurada.
2. **Novo evento**: nome do cliente, categoria, data, observações internas
   (nunca aparecem ao cliente) e, opcionalmente, uma data de expiração.
3. Ao salvar, um **código de 30 caracteres** é gerado automaticamente e
   exibido **uma única vez**, com botões de copiar (só código ou link
   completo). Depois dessa tela o código **não pode mais ser recuperado**
   em texto puro — nem pela fotógrafa.
4. Envie as fotos do evento (JPG/PNG/WebP, múltiplas de uma vez). O sistema
   gera automaticamente uma versão web (máx. 1600px) e guarda o original
   separado, fora da pasta pública.
5. No evento você pode: **revogar/reativar** o acesso, **gerar um novo
   código** (o antigo deixa de funcionar imediatamente), editar dados,
   excluir fotos/evento e ver o **histórico de acessos** (quando + IP).
6. Envie o link (ou só o código) para o cliente, ex.: `https://seudominio.com/galeria/AbCdEf...`

## Fluxo do cliente

- **Pelo link**: `/galeria/<código>` abre a galeria direto, com o mesmo
  visual (lightbox) do site.
- **Pelo campo da home**: na seção "Já é cliente? Acesse sua galeria" da
  página inicial, o cliente cola o código e é redirecionado para a galeria.
- Código inexistente, expirado ou revogado produzem **sempre a mesma
  resposta genérica** — ninguém consegue "testar" códigos e descobrir se um
  evento existe.

## Segurança — decisões implementadas

- **Código**: 30 caracteres URL-safe gerados com `secrets` (criptograficamente
  seguro, ~180 bits de entropia). No banco fica **apenas o hash SHA-256** —
  o texto claro existe somente na tela de criação.
- **Senha do admin**: hash `werkzeug` vindo de variável de ambiente; nunca
  em texto puro nem no código.
- **CSRF**: todos os formulários (incluindo o público) exigem token válido
  (Flask-WTF/CSRFProtect).
- **Rate limiting** no login e no endpoint público de validação
  (`/acesso`): 8 tentativas/minuto por IP. Em produção, use Redis via
  `RATELIMIT_STORAGE_URI`.
- **Upload**: nome sanitizado (`secure_filename`), allowlist de
  extensão/mimetype (imagens apenas) e validação real da imagem com Pillow.
  Nomes de arquivo são hex aleatório — URLs impossíveis de adivinhar.
- **Originais fora da web**: os arquivos originais ficam em
  `instance/uploads/originais/`, fora do `/static`. A troca futura por
  S3/Cloudinary (com URLs assinadas) exige mudar apenas `storage.py`.
- **Cabeçalhos**: `X-Content-Type-Options: nosniff`,
  `Referrer-Policy`, `X-Frame-Options: SAMEORIGIN` em toda resposta.

## Deploy no Render.com (pronto para usar) ✅

O projeto já vem adaptado para o Render: **Whitenoise** serve os arquivos
estáticos sem Nginx, **PostgreSQL** via `DATABASE_URL` automático, `Procfile`
com o comando de start e `render.yaml` (Blueprint) para deploy automatizado.

> O plano **free** do Render hiberna o serviço após ~15 min sem acesso — a
> primeira visita após a hibernação demora ~30-60 s para responder.

### Opção A — Deploy automático (Blueprint, recomendado)

1. Suba o projeto para um repositório GitHub (ou GitLab/Bitbucket).
2. No Render: **New → Blueprint** → conecte o repositório.
3. O Render lê o `render.yaml` e cria: o web service + o banco PostgreSQL.
4. Vá em **Environment** do web service e defina `ADMIN_PASSWORD_HASH`:
   - Gere o hash localmente com `flask --app app admin-password "sua-senha"`
     (ou `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('sua-senha'))"`).
   - Cole o resultado em `ADMIN_PASSWORD_HASH` (nunca a senha em texto puro).
5. **Deploy** e aguarde. O Render roda o build (instala requirements) e o
   start (`gunicorn ...`).
6. Rode a migração do banco uma vez no shell do Render:
   `flask --app app db upgrade` (ou via `flask db upgrade` no dashboard).
   > Dica: adicione um build command que já roda a migração:
   > `pip install -r requirements.txt && flask --app app db upgrade`
7. Pronto: `https://<seu-app>.onrender.com` (HTTPS automático) e o painel
   em `https://<seu-app>.onrender.com/admin`.

### Opção B — Manual (Web Service)

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app --worker-class gthread --threads 4 --workers 1 --timeout 120 --access-logfile -`
- **Banco:** New → PostgreSQL → o Render injeta `DATABASE_URL` automaticamente.
- **Variáveis de ambiente:** `SECRET_KEY` (Render pode gerar), `ADMIN_PASSWORD_HASH` (você define), `FLASK_DEBUG=0`.
- **Persistência das fotos (importante):** no Web Service, adicione um
  **Disk** (New → Disk) montado em `/opt/render/project/src/data` — o
  código usa `RENDER_DISK_PATH` automaticamente se definido. Sem disk, as
  fotos enviadas **somem a cada redeploy**.

### Variáveis de ambiente no Render

| Variável | Como definir |
|---|---|
| `SECRET_KEY` | **Generate value** (botão do Render) ou valor próprio |
| `ADMIN_PASSWORD_HASH` | Você cola o hash gerado localmente |
| `DATABASE_URL` | Automático (PostgreSQL do Render) |
| `FLASK_DEBUG` | `0` |
| `RATELIMIT_STORAGE_URI` | opcional: `redis://...` se usar Redis (senão `memory://`) |
| `RENDER_DISK_PATH` | Automático se você criar um Disk no serviço |

### Observações de produção

- **HTTPS:** o Render fornece certificado SSL automático — sem precisar de
  Nginx. O header `Strict-Transport-Security` é enviado automaticamente.
- **Rate limit:** com 1 worker (configuração padrão), `memory://` funciona.
  Se aumentar os workers, use Redis (`RATELIMIT_STORAGE_URI=redis://...`),
  senão os limites são contados por worker.
- **Backups:** o PostgreSQL do Render faz backups diários automáticos. As
  fotos ficam no Disk (faça backup manual se precisar).
- **Limite de upload:** `MAX_CONTENT_LENGTH` padrão 50 MB por requisição.

## Testes

```bash
# Testes unitários (geração/validação de código, status de evento, upload)
python -m unittest discover tests -v

# Fluxo completo automatizado (login → criar evento → upload → código → galeria)
python -m unittest tests.test_fluxo -v
```

Para testar o fluxo manualmente: crie um evento no `/admin`, envie fotos,
copie o código, abra o link `/galeria/<código>` em outra aba (ou use o campo
da home) e confirme que fotos erradas/expiradas/revogadas dão a mesma
mensagem genérica.

## O que já vem otimizado (mantido)

- **Compressão gzip** (Flask-Compress) em HTML/CSS/JS.
- **Cache de estáticos por 1 ano** no navegador. Se editar `style.css` ou
  `main.js` depois de publicar, renomeie o arquivo (ex: `style.v2.css`).
- Zero dependências de frontend pesadas; JS com `defer`; fonts com
  `font-display: swap`; `loading="lazy"` nas fotos.
- Site one-page: uma rota, sem round trips extras.

## Sistema de cores (60% roxo · 30% verde · 10% dourado)

Todas as cores centralizadas em `:root` no topo de `static/css/style.css`
(`--purple-900`, `--green-600`, `--gold-500`, etc.). Os estilos novos do
painel e das galerias privadas reutilizam exatamente esses tokens.

## Acessibilidade

- Link "Pular para o conteúdo", foco visível (`:focus-visible`), contraste
  verificado, respeita `prefers-reduced-motion`.
- O painel admin e as páginas de erro usam `noindex` para não aparecer no Google.
