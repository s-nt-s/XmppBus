#!/usr/bin/env python3

import re
import traceback
from os import chdir
from os.path import dirname, realpath
from textwrap import dedent

from xmppbot import XmppBot, CmdSearch, CmdBot, CmdMatch, CmdDefault
from xmppbot.basebot import Message

from core.dbbus import DBBus
from core.printer import Printer, StrPrinter
import logging

chdir(dirname(realpath(__file__)))


db = DBBus()
re_sp = re.compile(r"\s+")


class BusBot(XmppBot):

    def tune_reply(self, txt):
        return "```\n%s\n```" % txt

    @CmdSearch(r"(hola|\?$)", flags=re.IGNORECASE)
    def hola(self):
        return dedent('''
        ¡Hola!
        Escribe el número de una parada para consultar los autobuses que pasan por ella (ej: 435).
        Si quieres ver solo un autobús, añade a continuación dicho bus (ej: 435 51).
        Si quieres repetir la última consulta que hayas hecho escribe simplemente un punto (.).
        Si quieres guardar un marcador a tu consulta añade una palabra que empieze por # tras ella (ej: 435 51 #casa) y cuando escribas esa palabra se realizara la consulta guardada.
        Si no te acuerdas de tus marcadores guardados, escribe # y te los listare.
        También puedes consultar el itinerario de una línea escribiendo la palabra paradas seguida del número de linea (ej: paradas 51),
        o consultar el saldo de tu tarjeta de transporte escribiendo saldo.
        ''').strip()

    @CmdBot("paradas")
    def reply_paradas(self, *args):
        if len(args) == 0:
            return "Debes indicar una línea para usar este argumento"
        return StrPrinter().paradas(*args)

    @CmdBot("#")
    def marcadores(self, msg: Message):
        return StrPrinter().marcadores(msg.sender)

    @CmdBot("borrar")
    def borrar_marcador(self, msg: Message, *marcador):
        if len(marcador) == 0:
            return "¿Qué marcador quieres borrar? Escribelo despues de la palabra borrar."
        marcador = " ".join(marcador).lower()
        db.del_marcador(msg.sender, marcador)
        return "¡Marcador borrado!"

    @CmdMatch(r"^saldo(\s+[\d\s]+)?$", flags=re.IGNORECASE)
    def saldo(self, msg: Message, tarjeta):
        if not tarjeta:
            tarjeta = ""
        tarjeta = re.sub(r"\s+", "", tarjeta)
        if len(tarjeta) == 0:
            tarjeta = db.get_tarjeta(msg.sender)
            if tarjeta is None:
                return "Escriba el número de su tarjeta ( " + Printer.IMG_CARD + " ) después de la palabra saldo"
        else:
            db.set_tarjeta(msg.sender, tarjeta)
        return StrPrinter().card(tarjeta)

    @CmdMatch(r"^(\d+.*)")
    def reply_tiempos(self, msg: Message, text, save_history=True):
        text = re_sp.sub(" ", text).strip()
        slp = text.split("#", 1)
        marcador = slp[-1].strip() if len(slp) > 1 else None
        words = slp[0].strip().split()
        parada = words[0]
        lineas = sorted(set(words[1:]), key=lambda x: (
            int(x) if x.isdigit() else 99999999, x))

        reply = StrPrinter().times(parada, *lineas)

        if marcador:
            db.set_marcador(msg.sender, marcador.lower(),
                            parada + " " + " ".join(lineas))

        if save_history:
            for h in range(3 - 1, 0, -1):
                hs = db.get_marcador(msg.sender, "." * h)
                if hs:
                    db.set_marcador(msg.sender, "." * (h + 1), hs)

            db.set_marcador(msg.sender, ".", text)

        return reply

    @CmdDefault()
    def reply_else(self, msg: Message):
        marcador = msg.text.lower()
        txt2 = db.get_marcador(msg.sender, marcador)
        if not txt2 and marcador.startswith("#"):
            txt2 = db.get_marcador(msg.sender, marcador[1:])
        if txt2:
            save_history = not re.match(r"^\.+$", marcador)
            return self.reply_tiempos(msg, txt2, save_history=save_history)
        return dedent('''
            No he entendido el mensaje, ¿estas usando mensajes encriptados (OMEMO, OpenPGP, etc)?
            Por favor, desactiva el encriptado y escribe hola para ver las opciones.
        ''').strip()

    def command_error(self, msg: Message, error):
        if msg.sender in self.config.admin:
            return str(error) + "\n\n" + traceback.format_exc()
        return dedent('''
            Ha ocurrido un error inesperado. Por favor, vuelva a intentarlo más tarde.
            Si el error persiste deje un issue en https://github.com/s-nt-s/XmppBus/issues
        ''').strip()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    xmpp = BusBot("config.yml")
    xmpp.run()
