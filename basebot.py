#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
import re
import yaml
import logging
import os.path
import inspect

import sleekxmpp

sp = re.compile(r"\s+", re.MULTILINE | re.UNICODE)


def botcmd(*args, **kwargs):
    """Decorator for bot command functions"""

    def decorate(func, name=None):
        setattr(func, '_command', True)
        setattr(func, '_command_name', name or func.__name__)
        return func

    if len(args):
        return decorate(args[0], **kwargs)
    else:
        return lambda func: decorate(func, **kwargs)


class XmppBot(sleekxmpp.ClientXMPP):

    def __init__(self, config_path):
        with file(config_path, 'r') as f:
            self.config = yaml.load(f)
        sleekxmpp.ClientXMPP.__init__(
            self, self.config['user'], self.config['pass'])
        logging.basicConfig(level=self.config.get('LOG', logging.INFO),
                            format='%(levelname)-8s %(message)s')
        self.log = logging.getLogger()

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.auto_authorize = True
        self.auto_subscribe = True
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0004')  # Data Forms
        self.register_plugin('xep_0060')  # PubSub
        self.register_plugin('xep_0199')  # XMPP Ping
        if self.config.get('vcard', None):
            self.register_plugin('xep_0054')
        if self.config.get('avatar', None):
            if os.path.isfile(self.config['avatar']):
                self.register_plugin('xep_0084')
                self.register_plugin('xep_0153')
            else:
                del self.config['avatar']

        self.commands = {}
        for name, value in inspect.getmembers(self, inspect.ismethod):
            if getattr(value, '_command', False):
                name = getattr(value, '_command_name').lower()
                self.log.info('Registered command: %s' % name)
                self.commands[name] = value

    def get_cmd(self, text):
        cmd = text.split(' ', 1)[0].lower()
        if self.commands.get(cmd, None):
            return self.commands[cmd]
        return None

    def start(self, event):
        self.send_presence()
        self.get_roster()
        if self.config.get('vcard', None):
            vcard = self['xep_0054'].stanza.VCardTemp()
            vcard['JABBERID'] = self.boundjid.bare
            for f in self.config['vcard']:
                vcard[f] = self.config['vcard'][f]
            self['xep_0054'].publish_vcard(vcard)
        if self.config.get('avatar', None):
            avatar_data = None
            try:
                with open(self.config['avatar'], 'rb') as avatar_file:
                    avatar_data = avatar_file.read()
            except IOError:
                logging.debug('Could not load avatar')
            if avatar_data:
                avatar_id = self['xep_0084'].generate_id(avatar_data)
                info = {
                    'id': avatar_id,
                    'type': 'image/png',
                    'bytes': len(avatar_data)
                }
                self['xep_0084'].publish_avatar(avatar_data)
                self['xep_0084'].publish_avatar_metadata(items=[info])
                self['xep_0153'].set_avatar(
                    avatar=avatar_data, mtype='image/png')

    def message(self, msg):
        if msg['type'] in ('chat', 'normal') and msg['body'] and msg['from']:
            user = msg['from'].bare
            txt = sp.sub(" ", msg['body']).strip()
            if user != self.boundjid.bare and len(txt) > 0:

                cmd = self.get_cmd(txt)
                if cmd:
                    reply = cmd(user, txt)
                    self.send_message(msg, reply)
                    return

                txt = self.parse_message(user, txt)
                if txt:
                    txt = self.reply_message(user, txt)
                    if txt:
                        self.send_message(msg, txt)

    def send_message(self, msg, txt):
        msgreply = msg.reply(txt)
        formated = self.format_message(txt)
        if formated:
            msgreply["html"]["body"] = formated
        msgreply.send()

    def run(self):
        if self.connect():
            self.log.info("Bot started.")
            self.process(block=True)
        else:
            self.log.info("Unable to connect.")
