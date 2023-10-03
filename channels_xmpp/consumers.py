from channels_xmpp.protocol.xmpp.stream import Stream
from .protocol.conf import settings
from .protocol.utils import format_addr
from .protocol.xmpp.bosh import handle_bosh, disconnect_bosh
from .protocol.xmpp.websockets import handle_ws, disconnect_ws
from channels.consumer import AsyncConsumer, StopConsumer
from django.conf import settings as django_settings
from django.http.request import validate_host
from django.utils.functional import cached_property
from urllib.parse import urlparse
import asyncio
import inspect
import logging


try:
    from defusedxml import ElementTree as ET
    def parse_xml(text):
        return ET.fromstring(text, forbid_dtd=True)
except ImportError:
    from xml.etree import ElementTree as ET
    def parse_xml(text):
        return ET.fromstring(text)
# try to avoid some unnecessary conversions, though perhaps
# this really belongs in some Channels middleware


class proxy_ssl_header_cache:
    @cached_property
    def header(self):
        proxy_header = django_settings.SECURE_PROXY_SSL_HEADER
        if proxy_header is not None:
            proxy_header = proxy_header[0][5:].lower().encode()
        return proxy_header


proxy_ssl = proxy_ssl_header_cache()


def get_scope_secure(scope, secure_scheme):
    proxy_header = proxy_ssl.header
    if proxy_header:
        for hdr, val in scope['headers']:
            if hdr == proxy_header:
                value = val.decode()
                return (value == secure_scheme or
                        value == django_settings.SECURE_PROXY_SSL_HEADER[1])
        return False
    return scope['scheme'] == secure_scheme


def get_host(scope):
    for hdr, value in scope['headers']:
        if hdr == b'host':
            return value
    return None


def get_origin(scope):
    for hdr, value in scope['headers']:
        if hdr == b'origin':
            return value
    return None


def is_trusted_origin(origin):
    if not settings.ALLOW_WEBUSER_LOGIN:
        return False
    if origin is None:
        return True
    allowed_hosts = django_settings.ALLOWED_HOSTS
    if django_settings.DEBUG and not allowed_hosts:
        allowed_hosts = ["localhost", "127.0.0.1", "[::1]"]
    try:
        origin_host = urlparse(origin.decode()).hostname
        return validate_host(origin_host, allowed_hosts)
    except UnicodeDecodeError:
        return False


def get_addr(scope):

    try:
        x_forwarded_for = scope['readers'].get('x-forwarded-for').split(',')[0]
        return format_addr(x_forwarded_for, "proxied")
    except:
        pass

    client = scope['client']

    return format_addr(client[0], client[1])


class WSConsumer(AsyncConsumer):

    xep_plugin = [
    ]

    @property
    def stream(self) -> Stream:
        return self._stream
    
    @stream.setter
    def stream(self, value):
        self._stream = value
        if self._stream:
            self.register_plugins()

    def register_plugins(self):
        if not self._stream:
            return
        
        for plugin in getattr(self, 'xep_plugin', []):
            if isinstance(plugin, str):
                self.stream.register_plugin(plugin)
            elif inspect.isfunction(plugin):
                self.stream.register_plugin(
                    *plugin(self)
                )
            elif isinstance(plugin, (tuple, list)):
                name = plugin[0]
                arg = plugin[1]
                if isinstance(arg, dict):
                    self.stream.register_plugin(name, **arg)
                elif isinstance(arg, type):
                    self.stream.register_plugin(name, module=arg)
                else:
                    self.stream.register_plugin(name, *plugin[1:])
            else:
                raise ValueError("The object '%s' is not a valid plugin" % plugin)

    def is_secure(self):
        return get_scope_secure(self.scope, 'wss')

    def is_trusted(self):
        return is_trusted_origin(self.http_origin)

    async def get_user(self):
        return self.scope['user']

    async def close_socket(self):
        self.logger.debug('Close')
        await self.send({
            'type': 'websocket.close',
        })

    async def send_data(self, data):
        text = str(data)
        self.logger.debug('Send: %s', text)
        await self.send({
            'type': 'websocket.send',
            'text': text,
            'subprotocol': 'xmpp',
        })

    async def websocket_connect(self, event):
        self._stream = None

        subprotos = self.scope.get('subprotocols', None)

        if subprotos and 'xmpp' in subprotos:    
            print(subprotos)
            self.logger = logging.LoggerAdapter(
                logging.getLogger('xmppserver.transport.websockets'),
                {'client': get_addr(self.scope)})
            
            self.http_host = get_host(self.scope)
            self.http_origin = get_origin(self.scope)
            self.loop = asyncio.get_event_loop()

            self.logger.debug('Connected')
            await self.send({
                'type': 'websocket.accept',
                'subprotocol': 'xmpp',
            })
        else:
            await self.send({
                'type': 'websocket.close'
            })


    async def websocket_receive(self, event):
        text = event['text']
        self.logger.debug('Receive: %s', text)
        xml = parse_xml(text)
        await handle_ws(self, xml)

    async def websocket_disconnect(self, event):
        self.logger.debug('Disconnected')
        if self.stream is not None:
            self.stream.connection_lost()
        self.stream = None
        raise StopConsumer()
