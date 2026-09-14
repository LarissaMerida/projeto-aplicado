from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")
        labels = {
            "username": "Nome de usuário",
            "password1": "Senha",
            "password2": "Confirme a senha",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "username": "Nome de usuário",
            "password1": "Senha",
            "password2": "Confirme a senha",
        }
        help_texts = {
            "username": "Obrigatório. Até 150 caracteres.",
            "password1": "Sua senha deve ter pelo menos 8 caracteres e não pode ser muito comum.",
            "password2": "Digite a mesma senha novamente para confirmação.",
        }
        for field_name, field in self.fields.items():
            field.label = labels[field_name]
            field.help_text = help_texts[field_name]
            field.error_messages["required"] = "Este campo é obrigatório."
            field.widget.attrs["placeholder"] = field.label

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nome de usuário já está em uso.")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("As senhas não conferem.")
        return password2