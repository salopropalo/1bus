from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import render, redirect
from app_users.forms import AuthForm
from django.contrib.auth.views import LoginView, LogoutView


class AnotherLoginView(LoginView):
    template_name = 'users/login.html'


class AnotherLogoutView(LogoutView):
    next_page = '/'

def blocked_view(request):
    return render(request, 'users/blocked_user.html')

def logout_view(request):
    logout(request)
    return HttpResponse('Пока!')


def login_view(request):
    if request.method == 'POST':
        auth_form = AuthForm(request.POST)
        if auth_form.is_valid():
            username = auth_form.cleaned_data['username']
            password = auth_form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Привет')  # успешный вход
                else:
                    # если пользователь неактивен (в админке снят флажок is_active)
                    return redirect('inactive_user')
            else:
                auth_form.add_error('__all__', 'Ошибка! Неверно ввели данные!')
    else:
        auth_form = AuthForm()

    content = {
        'form': auth_form,
        'title': 'Вход пользователя',
    }
    return render(request, 'users/login.html', context=content)


def inactive_user_view(request):
    """Показывает страницу с картинкой, если пользователь не активен"""
    return render(request, 'users/inactive.html')