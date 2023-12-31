from django.apps import AppConfig
from django.utils.translation import pgettext_lazy

class SessionDBConfig(AppConfig):
    name = 'channels_xmpp.sessiondb'
    verbose_name = pgettext_lazy('xmpp', 'XMPP Sessions')

    def ready(self):
        from .hook import SessionHook, clear_old_sessions
        from ..protocol.hooks import set_hook
        set_hook('session', SessionHook, priority=1)
        clear_old_sessions()
