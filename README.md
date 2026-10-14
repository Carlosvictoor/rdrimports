# RDR Imports

Loja virtual com catálogo de produtos, carrinho, pagamento online pelo Mercado Pago e painel administrativo.

## Funcionalidades

**Loja**
- Catálogo por categorias e página de cada produto
- Carrinho de compras (adicionar, alterar quantidade, remover)
- Cadastro e login de clientes, com área "Minha conta"
- Checkout com pagamento pelo Mercado Pago e páginas de sucesso, falha e pendente
- Atualização automática do status do pedido via webhook do Mercado Pago
- Avaliações de produtos com nota em estrelas

**Painel admin** (`/admin`)
- Dashboard da loja
- Cadastro, edição e exclusão de categorias e produtos, com imagens
- Lista de pedidos, detalhes e alteração de status
- Gestão de usuários e permissões de administrador

**Segurança**
- Senhas com hash, proteção CSRF nos formulários (Flask-WTF)
- Limite de requisições contra abuso (Flask-Limiter)
- Cabeçalhos de segurança HTTP e Content Security Policy (Flask-Talisman)
- Sanitização de textos enviados por usuários (bleach)

## Tecnologias

- **Backend:** Python, Flask, Flask-Login, Flask-WTF, Flask-Migrate
- **Banco de dados:** SQLite com SQLAlchemy
- **Pagamentos:** SDK do Mercado Pago
- **Servidor de produção:** Waitress

## Estrutura

```
app.py          Criação da aplicação e configuração das extensões
config.py       Configurações (lidas do .env)
core/           Extensões e funções de segurança
models/         Usuário, categoria, produto, pedido e avaliação
routes/         Loja, carrinho, autenticação, pagamento, avaliações e admin
templates/      Páginas HTML (Jinja2)
static/         CSS, JavaScript e imagens
```

## Como rodar localmente

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # depois edite o .env com seus valores
python app.py
```

Acesse http://localhost:5000

Para rodar em modo produção no Windows, use `start_prod.bat`.

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave da aplicação, use um valor longo e aleatório |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Conta de administrador inicial |
| `MP_ACCESS_TOKEN` / `MP_PUBLIC_KEY` | Credenciais do Mercado Pago |
| `BASE_URL` | Endereço público do site (usado no webhook) |
| `FLASK_DEBUG` | `1` em desenvolvimento, `0` em produção |
