from django.urls import re_path


from .consumers import WSConsumer

ws_urlpatterns = [
    re_path(r'^ws/xmpp/$', WSConsumer.as_asgi()),
]
