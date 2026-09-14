# Projeto Aplicado

Aplicação web desenvolvida em Django com cadastro, autenticação, logout e uma
área interna protegida. O projeto usa Class-Based Views e formulários próprios
para manter as responsabilidades separadas.

## Objetivo e arquitetura

O projeto demonstra uma aplicação web Django organizada para execução local,
em container Docker e em produção atrás de um servidor web. A aplicação é
composta por:

- Django 5 para rotas, autenticação, sessões, templates e acesso ao banco.
- PostgreSQL em produção, definido pelo `docker-compose.yml`.
- SQLite disponível para desenvolvimento local.
- Gunicorn como servidor de aplicação no container.
- Nginx ou Apache como camada pública de produção, conforme a configuração da
	infraestrutura.
- GitHub Actions para integração contínua e implantação contínua.

O fluxo esperado é: desenvolvimento assistido por IA, commit e push para o
GitHub, execução do CI, criação da imagem Docker e deploy no servidor por SSH.

## Funcionalidades

- Página inicial pública em `/`
- Login em `/login/`
- Cadastro em `/cadastro/`
- Área interna protegida em `/area-interna/`
- Logout via `POST` em `/logout/`

## Execução local

```bash
python -m venv venv
venv/bin/pip install -e .
venv/bin/python src/manage.py migrate
venv/bin/python src/manage.py runserver
```

A aplicação ficará disponível em `http://127.0.0.1:8000/`.

Para executar com Docker, defina as variáveis de ambiente necessárias e use:

```bash
docker compose up --build
```

As configurações sensíveis são fornecidas por variáveis de ambiente, incluindo
`DJANGO_SECRET_KEY`, `DB_PASSWORD` e `DJANGO_DEBUG`.

## Organização principal

- `src/projeto_aplicado/forms.py`: formulário de cadastro e suas validações.
- `src/projeto_aplicado/views.py`: Class-Based Views da aplicação.
- `src/projeto_aplicado/urls.py`: rotas públicas, de autenticação e da área protegida.
- `src/templates/`: templates HTML da home, autenticação e área interna.
- `docker-compose.yml`: serviços web e PostgreSQL.
- `Dockerfile`: imagem da aplicação.
- `.github/workflows/ci.yml`: validações, auditoria e build da imagem.
- `.github/workflows/cd.yml`: deploy da imagem aprovada no servidor.

## CI/CD e segredos

O workflow de CI é executado em push e pull request para `main`. Ele valida o
lock do Poetry, instala as dependências, executa os hooks de pre-commit e
constrói a imagem Docker. Em push, a imagem é publicada no GitHub Container
Registry.

O workflow de CD é executado após um CI bem-sucedido na branch `main`. Ele usa
`appleboy/ssh-action` para acessar o servidor, fazer login no GHCR, baixar a
imagem correspondente ao commit e reiniciar os serviços Docker.

Os valores sensíveis são configurados em GitHub Secrets, incluindo
`SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `SSH_PORT`, `GHCR_USERNAME`,
`GHCR_TOKEN` e `DEPLOY_PATH`. Nenhuma chave privada ou credencial real deve ser
adicionada ao código.

## Mitigações OWASP

As medidas abaixo foram implementadas diretamente no código e devem ser
consideradas em conjunto com a configuração segura do ambiente de produção.

### 1. A01:2025 - Broken Access Control

A área interna não fica disponível apenas por esconder um link na interface.
O acesso é controlado no servidor pelo `LoginRequiredMixin`.

Localização da mitigação:

- `src/projeto_aplicado/views.py`, classe `ProtectedView`.
- `src/projeto_aplicado/urls.py`, rota `area-interna/`.
- `src/projeto_aplicado/settings.py`, configuração `LOGIN_URL`.

Quando uma pessoa não autenticada acessa `/area-interna/`, o Django bloqueia a
view e redireciona para o login, preservando o destino original no parâmetro
`next`.

### 2. A04:2025 - Cryptographic Failures

Senhas não são armazenadas em texto puro. O `RegisterForm` herda de
`UserCreationForm`, e o `form.save()` usa o sistema de autenticação do Django
para armazenar a senha com hash e salt. O login valida a senha usando o mesmo
mecanismo do framework.

Localização da mitigação:

- `src/projeto_aplicado/forms.py`, classe `RegisterForm`.
- `src/projeto_aplicado/views.py`, método `RegisterView.form_valid()`.
- `src/projeto_aplicado/settings.py`, lista `AUTH_PASSWORD_VALIDATORS`.

Além disso, os validadores impedem senhas muito curtas, comuns, numéricas ou
semelhantes aos dados do usuário.

### 3. A05:2025 - Injection

O nome de usuário é consultado pelo ORM do Django, sem montar SQL por
concatenação de strings. O conteúdo exibido nos templates também passa pelo
autoescape padrão do mecanismo de templates, reduzindo o risco de injeção de
HTML/JavaScript em valores vindos do usuário.

Localização da mitigação:

- `src/projeto_aplicado/forms.py`, método `RegisterForm.clean_username()` e
	consulta `User.objects.filter(...)`.
- `src/templates/home.html` e `src/templates/protected.html`, onde valores do
	usuário são renderizados com as variáveis padrão do template Django.
- `src/projeto_aplicado/settings.py`, configuração `TEMPLATES` com
	`APP_DIRS=True`.

### 4. A07:2025 - Authentication Failures

O fluxo de autenticação rejeita credenciais incorretas e usuários inativos,
rotaciona o identificador de sessão após o login e encerra a sessão no logout.
O acesso à área interna também depende da autenticação no servidor, e não
somente da interface.

Localização da mitigação:

- `src/projeto_aplicado/views.py`, classes `LoginView`, `LogoutView` e
	`ProtectedView`.
- `src/projeto_aplicado/settings.py`, configurações `LOGIN_URL`,
	`LOGIN_REDIRECT_URL` e `LOGOUT_REDIRECT_URL`.
- `src/projeto_aplicado/tests.py`, testes de login inválido, usuário inativo,
	rotação de sessão e logout.

### Controles adicionais

Os formulários de login, cadastro e logout incluem `{% csrf_token %}`. O
`CsrfViewMiddleware`, configurado em `src/projeto_aplicado/settings.py`,
valida esses tokens e protege as operações `POST` contra requisições forjadas.

## Desenvolvimento assistido por IA

O desenvolvimento, a refatoração e a auditoria desta aplicação foram
realizados com auxílio de um assistente de programação baseado em IA integrado
ao VS Code, equivalente ao ambiente de desenvolvimento assistido indicado no
escopo. A IA foi utilizada para implementar o fluxo de autenticação, revisar a
separação entre formulários e Class-Based Views, analisar as mitigações OWASP e
apoiar a validação do código.

## Validação

Os comandos mínimos para validar a aplicação são:

```bash
venv/bin/python src/manage.py check
venv/bin/python src/manage.py test projeto_aplicado
pre-commit run --all-files
```

Os testes de segurança estão em `src/projeto_aplicado/tests.py` e verificam:

- bloqueio da área interna para usuários anônimos;
- acesso permitido somente após autenticação;
- bloqueio de cadastro e logout sem token CSRF;
- armazenamento de senhas com hash;
- rejeição de senhas fracas, confirmações divergentes e usuários duplicados;
- rejeição de nomes de usuário acima do limite permitido;
- bloqueio de login para usuários inativos;
- prevenção de redirecionamento para host externo após o login;
- rotação do identificador de sessão após autenticação;
- escape de conteúdo fornecido pelo usuário nos templates;
- cabeçalho `X-Frame-Options` contra clickjacking;
- presença de tokens CSRF nos formulários;
- remoção da sessão após o logout.

O teste funcional confirma que `/area-interna/` redireciona pessoas não
autenticadas para o login, responde com sucesso para usuários autenticados e
deixa de ser acessível depois do logout.
