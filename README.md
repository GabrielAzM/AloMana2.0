# Alo!Mana? 2.0

Prototipo web em Flask com fachada de e-commerce para registro discreto de ocorrencias, checkout com cupom 100% e painel administrativo.

## Stack

- Flask + Jinja2
- Flask-SQLAlchemy
- SQLite (padrao)
- Gunicorn (producao/deploy)
- HTML/CSS/JS no frontend

## Funcionalidades entregues

- Loja:
  - Home (`/`)
  - Produtos com busca/filtro (`/produtos`)
  - Categorias (`/kits`, `/skincare`, `/maquiagem`)
  - Detalhe de produto (`/produto/<slug>`)
  - Carrinho (`/carrinho`)
  - Checkout (`/checkout`) com cupom automatico de 100%
- Login da usuaria e acompanhamento:
  - Cadastro (`/cadastro`)
  - Login (`/login`)
  - Meus pedidos (`/meus-pedidos`)
  - Detalhe do pedido (`/meus-pedidos/<id>`)
- Painel admin:
  - Login (`/admin/login`)
  - Ocorrencias (`/admin/ocorrencias`)
  - Triagem/status/notas
  - Mapeamento produto -> categoria/urgencia

## Executar localmente

1. Instalar dependencias:
   - `python -m pip install -r requirements.txt`
2. Rodar a app:
   - `python run.py`
3. Acessar:
   - Loja: `http://127.0.0.1:5000/`
   - Admin: `http://127.0.0.1:5000/admin/login`

## Credenciais padrao

- Admin:
  - usuario: `admin`
  - senha: `admin123`
- Usuario demo:
  - usuario: `usuario_demo`
  - email: `usuario@alomana.local`
  - senha: `usuario123`

## Deploy no Render

O projeto ja inclui os arquivos de deploy:

- `render.yaml`
- `Procfile`
- `wsgi.py`

### Opcao 1: Blueprint (recomendado)

1. No Render, clique em **New +** -> **Blueprint**.
2. Conecte este repositorio.
3. O Render vai ler `render.yaml` e criar o web service.

### Opcao 2: Web Service manual

1. **New +** -> **Web Service**.
2. Build Command:
   - `python -m pip install -r requirements.txt`
3. Start Command:
   - `gunicorn --bind 0.0.0.0:$PORT wsgi:app`
4. Variaveis de ambiente recomendadas:
   - `SECRET_KEY` (obrigatorio em producao)
   - `ADMIN_DEFAULT_USERNAME`
   - `ADMIN_DEFAULT_PASSWORD`
   - `USER_DEFAULT_USERNAME`
   - `USER_DEFAULT_EMAIL`
   - `USER_DEFAULT_PASSWORD`
   - `DATABASE_URL` (opcional; se nao definir, usa SQLite local)

> Observacao: no Render, SQLite em disco local e efemero. Para persistencia real apos reinicios/deploys, use banco gerenciado e ajuste `DATABASE_URL`.

## Observacao de avaliacao

A instituicao foi anonimizada nas telas com a frase:
- `informacao omitida e anonimizada para avaliacao`
