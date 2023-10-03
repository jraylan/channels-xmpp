from django.apps import AppConfig
from django.utils.translation import pgettext_lazy

class RosterDBConfig(AppConfig):
    name = 'channels_xmpp.rosterdb'
    verbose_name = pgettext_lazy('xmpp', 'XMPP Rosters')

    def ready(self):
        from .hook import RosterHook
        from ..protocol.hooks import set_hook
        set_hook('roster', RosterHook, priority=1)
