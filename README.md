# Projeto Aplicado

Aplicação web desenvolvida em Django com cadastro, autenticação, logout e uma
área interna protegida. O projeto usa Class-Based Views e formulários próprios
para manter as responsabilidades separadas.

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

## Organização principal

- `src/projeto_aplicado/forms.py`: formulário de cadastro e suas validações.
- `src/projeto_aplicado/views.py`: Class-Based Views da aplicação.
- `src/projeto_aplicado/urls.py`: rotas públicas, de autenticação e da área protegida.
- `src/templates/`: templates HTML da home, autenticação e área interna.

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

### Controles adicionais

Os formulários de login, cadastro e logout incluem `{% csrf_token %}`. O
`CsrfViewMiddleware`, configurado em `src/projeto_aplicado/settings.py`,
valida esses tokens e protege as operações `POST` contra requisições forjadas.
