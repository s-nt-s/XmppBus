#!/usr/bin/env python3

from core.dbbus import DBBus
from core.printer import StrPrinter
import logging

from os import chdir
from os.path import dirname, realpath

logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("slixmpp.stringprep").setLevel(logging.CRITICAL)

from xmppbot import XmppMsg

chdir(dirname(realpath(__file__)))

db = DBBus()
prnt = StrPrinter()
xmpp = XmppMsg("config.yml")

for t in db.get_tarjetas():
    msg = prnt.card_aviso(t.tarjeta, umbral=4)
    if msg:
        xmpp.to = t.user
        xmpp.msg = msg
        xmpp.send()
