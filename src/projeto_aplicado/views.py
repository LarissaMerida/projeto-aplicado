from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from projeto_aplicado.forms import RegisterForm


class HomeView(TemplateView):
    template_name = "home.html"


class ProtectedView(LoginRequiredMixin, TemplateView):
    template_name = "protected.html"
    login_url = reverse_lazy("login")


class LoginView(auth_views.LoginView):
    template_name = "registration/login.html"


class LogoutView(auth_views.LogoutView):
    pass


class AnonymousOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_anonymous

    def handle_no_permission(self):
        return redirect("home")


class RegisterView(AnonymousOnlyMixin, CreateView):
    form_class = RegisterForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response