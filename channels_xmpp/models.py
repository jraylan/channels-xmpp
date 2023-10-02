# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings as django_settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _



class XMPPUser(models.Model):
    sys_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_(u'Usuário'),
        blank=True, null=True,
        on_delete=models.CASCADE,
        related_name="xmpp_user")
    contact = models.ForeignKey(
        "chatapp.Contact",
        verbose_name=_("Contato"),
        blank=True, null=True,
        on_delete=models.CASCADE,
        related_name="xmpp_user")
    

    @property
    def user(self):
        return self.user or self.contact
    
    @property
    def jid(self):
        namespace = self.user._meta.models_name
        return f'{self.user.id}.{namespace}'
    

class XMPPRoom(models.Model):
    name = models.CharField(
        _("Nome"),
        max_length=100
    )
    
    members = models.ManyToManyField(
        XMPPUser,
        through="XMPPRoomMember",
        through_fields=('room', 'member')
    )


class XMPPRoomMember(models.Model):
    room = models.ForeignKey(XMPPRoom, on_delete=models.CASCADE)
    member = models.ForeignKey(XMPPUser, on_delete=models.CASCADE)
    role = models.CharField(
        _("Papel"),
        max_length=100,
        choices=(
            (_('Moderador'), "Moderator"),
            (_('Nenhuma'), "None"),
            (_('Participante'), "Participant"),
            (_('Visitante'), "Visitor")
        )
    )

    class Meta:
        verbose_name = _("XMPP Room Member")
        verbose_name_plural = _("XMPP Room Members")

    def __str__(self):
        return self.name


def get_chat_domain():
    from .protocol.conf import settings
    domain = settings.DOMAIN
    if domain:
        return domain
    
    return 'localhost'

@receiver(post_delete, sender=django_settings.AUTH_USER_MODEL)
def user_deleted(sender, instance, **kwargs):
    from .protocol.hooks import get_hook
    auth_hook = get_hook('auth')
    username = auth_hook.get_webuser_username(instance)
    if username is not None:
        from .protocol.xmpp.dummy import DummyStream
        # The DummyStream is able to access the database
        # and communicate with other XMPP streams.
        # Just tell it that the user is gone.
        stream = DummyStream()
        stream.boundjid.username = username
        stream.boundjid.domain = get_chat_domain()
        stream.user_deleted()
        stream.dispose()
