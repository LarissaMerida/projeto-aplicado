from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from projeto_aplicado.forms import RegisterForm


User = get_user_model()


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.password = "UmaSenhaForte123!"
        self.user = User.objects.create_user(
            username="usuario_seguro",
            password=self.password,
        )

    def csrf_token_for(self, url):
        self.client.get(url)
        return self.client.cookies["csrftoken"].value

    def test_area_interna_bloqueia_usuario_anonimo(self):
        response = self.client.get(reverse("protected"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('protected')}",
        )

    def test_area_interna_permite_usuario_autenticado(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("protected"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_cadastro_valido_cria_usuario_e_inicia_sessao(self):
        csrf_token = self.csrf_token_for(reverse("register"))
        response = self.client.post(
            reverse("register"),
            {
                "username": "novo_usuario",
                "password1": self.password,
                "password2": self.password,
                "csrfmiddlewaretoken": csrf_token,
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("home"))
        created_user = User.objects.get(username="novo_usuario")
        self.assertEqual(int(self.client.session["_auth_user_id"]), created_user.pk)

    def test_usuario_autenticado_nao_pode_abrir_cadastro(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("register"))

        self.assertRedirects(response, reverse("home"))

    def test_login_com_credenciais_validas_inicia_sessao(self):
        csrf_token = self.csrf_token_for(reverse("login"))
        response = self.client.post(
            reverse("login"),
            {
                "username": self.user.username,
                "password": self.password,
                "csrfmiddlewaretoken": csrf_token,
            },
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            self.user.pk,
        )

    def test_login_com_senha_incorreta_nao_inicia_sessao(self):
        csrf_token = self.csrf_token_for(reverse("login"))
        response = self.client.post(
            reverse("login"),
            {
                "username": self.user.username,
                "password": "SenhaErrada123!",
                "csrfmiddlewaretoken": csrf_token,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Por favor, entre com um usuário")

    def test_cadastro_post_sem_csrf_e_bloqueado(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "novo_usuario",
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="novo_usuario").exists())

    def test_logout_post_sem_csrf_e_bloqueado(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertEqual(response.status_code, 403)
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_logout_nao_aceita_get(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_cadastro_usa_hash_para_armazenar_senha(self):
        form = RegisterForm(
            data={
                "username": "novo_usuario",
                "password1": self.password,
                "password2": self.password,
            }
        )

        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))

    def test_formulario_rejeita_senha_fraca_e_senhas_diferentes(self):
        weak_password_form = RegisterForm(
            data={
                "username": "novo_usuario",
                "password1": "12345678",
                "password2": "12345678",
            }
        )
        mismatched_password_form = RegisterForm(
            data={
                "username": "outro_usuario",
                "password1": self.password,
                "password2": "senha-diferente",
            }
        )

        self.assertFalse(weak_password_form.is_valid())
        self.assertIn("password2", weak_password_form.errors)
        self.assertFalse(mismatched_password_form.is_valid())
        self.assertIn("password2", mismatched_password_form.errors)

    def test_formulario_rejeita_usuario_duplicado(self):
        form = RegisterForm(
            data={
                "username": self.user.username,
                "password1": self.password,
                "password2": self.password,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("já está em uso", form.errors["username"][0])

    def test_template_escapa_conteudo_fornecido_pelo_usuario(self):
        self.user.username = "<script>alert('x')</script>"
        self.user.save(update_fields=["username"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("protected"))

        self.assertNotContains(response, "<script>alert('x')</script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_logout_remove_a_sessao(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse("logout"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", client.session)