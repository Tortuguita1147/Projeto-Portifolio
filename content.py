# -*- coding: utf-8 -*-
"""
Conteúdo do site — Rayane Yasmin Fotografia.

Todo o texto do site vive neste arquivo, separado das rotas e dos templates.
Para atualizar qualquer texto, valor ou item da galeria, edite apenas aqui —
não é necessário mexer em app.py nem nos templates HTML.

Campos marcados com "TODO:" precisam da confirmação da Rayane antes de publicar.
"""

SITE = {
    "nome": "Rayane Yasmin",
    "titulo_aba": "Rayane Yasmin Fotografia | Ensaios sensíveis e autênticos",
    "descricao_meta": (
        "Fotografia sensível e autêntica em ensaios femininos, casais, "
        "casamentos, famílias e eventos. Conheça o trabalho da Rayane Yasmin."
    ),
    "whatsapp_numero": "5516981074065",  # TODO: número real, com DDI+DDD, sem espaços
    "whatsapp_exibicao": "(16) 98107-4065",  # TODO
    "instagram_usuario": "sntos_ray_",  # TODO
    "email": "@email",  # TODO
    "cidade_base": "Araraquara",  # TODO
}

HERO = {
    "titulo": "Rayane Yasmin",
    "subtitulo": "Fotografia que sente. Memórias que ficam.",
    "cta_primario": "Ver portfólio",
    "cta_secundario": "Solicitar orçamento",
}

SOBRE = {
    "texto": [
        "Paragrafo sobre a Ray"
    ],
    "filosofia": (
        "filosofia"
    ),
}

ESPECIALIDADES = [
    {
        "titulo": "ESPECIALIDADE 1",
        "texto": "lá lá lá",
    },
    {
        "titulo": "ESPECIALIDADE 2",
        "texto": "lá lá lá",
    },
    {
        "titulo": "ESPECIALIDADE 3",
        "texto": "lá lá lá",
    },
    {
        "titulo": "ESPECIALIDADE 4",
        "texto": "lá lá lá",
    },
    {
        "titulo": "ESPECIALIDADE 5",
        "texto": "lá lá lá",
    },
    {
        "titulo": "ESPECIALIDADE 6",
        "texto": "lá lá lá",
    },
]

# Galeria em formato bento: 4 estilos de foto + 1 vídeo.
# Layout (definido em CSS pelos seletores .gallery-card--<id>):
#   ┌─────────┬───────────────┬─────────┐
#   │ gestante│   CASAMENTO   │ 15 anos │ <- gestante à esquerda, casamento no meio (principal/2x1)
#   │         │  (PRINCIPAL/  ├─────────┤
#   ├─────────┤   BIG 2 rows) │anivers. │
#   │  Vídeos │               │         │
#   └─────────┴───────────────┴─────────┘
# - casamento é o "estilo principal" (carta de apresentação).
# - À direita ficam os 2 estilos "menores" (15 anos + aniversário).
# - À esquerda, no canto inferior, fica o card de vídeo.
# A ordem dos itens abaixo não importa para o layout — a posição é
# controlada pelas classes CSS, e o template usa `loop.first` apenas
# para marcar o card "principal" visualmente.
# O modal abre todas as referências (lista `fotos`) do estilo clicado,
# então mantenha 6+ fotos em cada categoria para o modal ficar rico.
GALERIA = [
    # Estilo principal — fica no meio, em destaque (BIG 2 rows).
    {
        "id": "casamento",
        "categoria": "Casamento",
        "principal": True,
        "capa": "img/Foto_teste.jpg",
        "fotos": [
            "img/Foto_teste.jpg", "img/Foto_teste.jpg", "img/Foto_teste.jpg",
            "img/Foto_teste.jpg", "img/Foto_teste.jpg", "img/Foto_teste.jpg",
            "img/Foto_teste.jpg", "img/Foto_teste.jpg", "img/Foto_teste.jpg",
        ],
    },
    # Estilo menor — canto direito superior.
    {
        "id": "15anos",
        "categoria": "15 anos",
        "capa": "img/Foto_teste.jpg",
        "fotos": [
            "img/Foto_teste.jpg", "img/Foto_teste.jpg", "img/Foto_teste.jpg",
            "img/Foto_teste.jpg", "img/Foto_teste.jpg", "img/Foto_teste.jpg",
        ],
    },
    # Estilo menor — canto direito inferior.
    {
        "id": "aniversario",
        "categoria": "Aniversário",
        "capa": "img/Foto_teste.jpg",
        "fotos": [
            "img/Foto_teste.jpg", "img/Foto_teste.jpg", "img/Foto_teste.jpg",
            "img/Foto_teste.jpg", "img/Foto_teste.jpg", "img/Foto_teste.jpg",
        ],
    },
    # Estilo menor — canto esquerdo superior (lado esquerdo = "lado").
    {
        "id": "gestante",
        "categoria": "Ensaio de gestante",
        "capa": "img/Foto_teste.jpg",
        "fotos": [
            "img/Foto_teste.jpg", "img/Foto_teste.jpg", "img/Foto_teste.jpg",
            "img/Foto_teste.jpg", "img/Foto_teste.jpg", "img/Foto_teste.jpg",
        ],
    },
    # Vídeo — canto esquerdo inferior (junto com a 4ª foto no "lado").
    {
        "id": "videos",
        "categoria": "Vídeos sobre nós",
        "tipo": "video",
        "capa": "img/Foto_teste.jpg",
        # TODO: trocar pelo link real do canal/playlist do YouTube
        "video_url": "https://www.youtube.com/@rayaneyasmin",
    },
] 

DIFERENCIAIS = [
    {
        "titulo": "Diferença 1",
        "texto": "Ela é linda tá",
    },
    {
        "titulo": "Diferença 2",
        "texto": "Ela é cheirosa tá",
    },
    {
        "titulo": "Diferença 3",
        "texto": "Ela tem um coração enorme tá",
    },
    {
        "titulo": "Diferença 4",
        "texto": "Ela é muitooo mas muito lgl",
    },
    {
        "titulo": "Diferença 5",
        "texto": "Ela é uma pessoa incrivel",
    },
    {
        "titulo": "Diferença 6",
        "texto": "Ela é minha namorada",
    },
]

PROCESSO = [
    {
        "numero": "01",
        "titulo": "Yes",
        "texto": "Yes",
    },
    {
        "numero": "02",
        "titulo": "Yes",
        "texto": "Yes",
        
    },
    {
        "numero": "03",
        "titulo": "Yes",
        "texto": "Yes",
    },
    {
        "numero": "04",
        "titulo": "Yes",
        "texto": "Yes"
    },
    {
        "numero": "05",
        "titulo": "Yes",
        "texto": "Yes"
    },
    {
        "numero": "06",
        "titulo": "Yes",
        "texto": "Yes"
    },
]

DEPOIMENTOS = [
    {
        "texto": "Quero ser a pessoa pra quem você volta correndo. Porque eu te amo.",
        "autor": "Cassie",
        "contexto": "Continência ao Amor",
    },
    {
        "texto": "A gente prometeu cuidar um do outro.",
        "autor": "Cassie",
        "contexto": "Continência ao Amor",
    },
    {
        "texto": "O coração decide tomar conta de tudo, mesmo quando a mente tinha outros planos.",
        "autor": "Cassie",
        "contexto": "Continência ao Amor",
    },
]

PACOTES = [
    {
        "nome": "Básico",
        "destaque": False,
        "descricao": "Ideal para quem quer um registro simples e objetivo.",
        "itens": [
            "Duração: 1 hora",
            "20 fotos editadas em alta resolução",
            "1 local de escolha",
            "Entrega em até 15 dias úteis",
        ],
        "preco": "Sob consulta",  # TODO: valor real
    },
    {
        "nome": "Essencial",
        "destaque": True,
        "descricao": "O equilíbrio ideal entre tempo, variedade e entrega.",
        "itens": [
            "Duração: 2 horas",
            "40 fotos editadas em alta resolução",
            "Até 2 locais ou looks",
            "Prévia digital em 48h",
            "Entrega completa em até 15 dias úteis",
        ],
        "preco": "Sob consulta",  # TODO: valor real
    },
    {
        "nome": "Premium",
        "destaque": False,
        "descricao": "Para quem quer viver a experiência completa, sem "
        "pressa de tempo.",
        "itens": [
            "Duração: 3 a 4 horas",
            "70 fotos editadas em alta resolução",
            "Múltiplos locais ou looks",
            "Direção de estilo e poses personalizada",
            "Prévia digital em 48h",
            "Entrega completa em até 20 dias úteis",
        ],
        "preco": "Sob consulta",  # TODO: valor real
    },
]

FAQ = [
    {
        "pergunta": "Quanto tempo demora para receber as fotos?",
        "resposta": "O prazo de entrega varia conforme o pacote escolhido, "
        "mas em média leva de 15 a 20 dias úteis. Ensaios maiores, como "
        "casamentos, podem levar um pouco mais — o prazo exato é sempre "
        "combinado antes do ensaio.",
    },
    {
        "pergunta": "Como escolho quais fotos serão editadas?",
        "resposta": "Após o ensaio, você recebe uma galeria online com "
        "todas as fotos em boa qualidade para visualização. A partir dela, "
        "você seleciona suas favoritas dentro da quantidade incluída no "
        "pacote — sem pressa, no seu tempo.",
    },
    {
        "pergunta": "E se chover no dia do ensaio?",
        "resposta": "Sem problema. Em caso de chuva ou condições climáticas "
        "que comprometam o ensaio ao ar livre, remarcamos a data sem "
        "nenhum custo adicional, priorizando sua próxima disponibilidade.",
    },
    {
        "pergunta": "Você realiza ensaios fora da cidade?",
        "resposta": "Sim! Ensaios fora de São Paulo são bem-vindos — pode "
        "haver uma taxa de deslocamento conforme a distância, sempre "
        "informada e combinada antes da confirmação.",
    },
    {
        "pergunta": "Como funciona o pagamento?",
        "resposta": "Geralmente é solicitado um sinal para reserva de data, "
        "com o restante pago próximo à data do ensaio ou na entrega — as "
        "condições são combinadas diretamente no orçamento.",
    },
]
