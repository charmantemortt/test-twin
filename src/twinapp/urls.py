from django.urls import path
from .views import form_view, twin_webhook

urlpatterns = [
    path('', form_view, name='form'),
    path('twin-webhook/', twin_webhook, name='webhook'),
]
