
import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_GET, require_POST

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


def serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }


@ensure_csrf_cookie
@require_GET
def csrf_token(request):
    return JsonResponse({
        'csrfToken': get_token(request)
    })


@csrf_protect
@require_POST
def login_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {'detail': 'Некорректный формат запроса'},
            status=400
        )

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return JsonResponse(
            {'detail': 'Введите логин и пароль'},
            status=400
        )

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is None:
        return JsonResponse(
            {'detail': 'Неверный логин или пароль'},
            status=401
        )

    login(request, user)

    return JsonResponse({
        'user': serialize_user(user)
    })


@csrf_protect
@require_POST
def logout_view(request):
    logout(request)

    return JsonResponse({
        'detail': 'Вы вышли из системы'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response(serialize_user(request.user))
