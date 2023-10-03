# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChannelsXmppConfig(AppConfig):
    name = 'channels_xmpp'
    verbose_name = _('Channels XMPP Server')
