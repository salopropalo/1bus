from django.shortcuts import render
from .models import BusductType, InfoBlock

def busduct_home(request):
    types = BusductType.objects.filter(is_active=True)
    blocks = InfoBlock.objects.filter(is_active=True)
    context = {
        'types': types,
        'blocks': blocks,
    }
    return render(request, 'busducts/header_home.html', context)