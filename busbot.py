#!/usr/bin/env python3

import re
import traceback
from os import chdir
from os.path import dirname, realpath
from textwrap import dedent

from xmppbot import XmppBot, botcmd

from core.dbbus import DBBus
from core.printer import Printer, StrPrinter

chdir(dirname(realpath(__file__)))


db = DBBus()


class BusBot(XmppBot):

    def tune_reply(self, txt):
        return "```\n%s\n```" % txt

    @botcmd(regex=re.compile(r"(hola|\?$)", re.IGNORECASE), rg_mode="search")
    def hola(self, *args, **kwargs):
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

    @botcmd(name="paradas")
    def reply_paradas(self, linea, *args, user, **kwargs):
        return StrPrinter().paradas(linea, *args)

    @botcmd(name="#")
    def marcadores(self, *args, user, **kwargs):
        return StrPrinter().marcadores(user)

    @botcmd(name="borrar")
    def borrar_marcador(self, *marcador, user, **kwargs):
        if len(marcador) == 0:
            return "¿Qué marcador quieres borrar? Escribelo despises de la palabra borrar."
        marcador = " ".join(marcador).lower()
        db.del_marcador(user, marcador)
        return "¡Marcador borrado!"

    @botcmd(regex=re.compile(r"^saldo(\s+[\d\s]+)?$", re.IGNORECASE), rg_mode="match")
    def saldo(self, tarjeta, *args, user, **kwargs):
        if not tarjeta:
            tarjeta = ""
        tarjeta = re.sub(r"\s+", "", tarjeta)
        if len(tarjeta) == 0:
            tarjeta = db.get_tarjeta(user)
            if tarjeta is None:
                return "Escriba el número de su tarjeta ( " + Printer.IMG_CARD + " ) después de la palabra saldo"
        else:
            db.set_tarjeta(user, tarjeta)
        return StrPrinter().card(tarjeta)

    @botcmd(regex=re.compile(r"^(\d+.*)"), rg_mode="match")
    def reply_tiempos(self, *args, user, text, **kwargs):
        slp = text.split("#", 1)
        marcador = slp[-1].strip() if len(slp) > 1 else None
        words = slp[0].strip().split(" ")
        parada = words[0]
        lineas = sorted(set(words[1:]), key=lambda x: (
            int(x) if x.isdigit() else 99999999, x))

        reply = StrPrinter().times(parada, *lineas)

        if marcador:
            db.set_marcador(user, marcador.lower(),
                            parada + " " + " ".join(lineas))

        if args is None or len(args) == 0 or not re.match(r"^\.+$", args[0]):
            for h in range(3 - 1, 0, -1):
                hs = db.get_marcador(user, "." * h)
                if hs:
                    db.set_marcador(user, "." * (h + 1), hs)

            db.set_marcador(user, ".", text)

        return reply

    @botcmd(regex=re.compile(r"^(\D+.*)$"), rg_mode="match")
    def reply_else(self, *args, user, text, **kwargs):
        marcador = text.lower()
        txt2 = db.get_marcador(user, marcador)
        if not txt2 and marcador.startswith("#"):
            txt2 = db.get_marcador(user, marcador[1:])
        if txt2:
            return self.reply_tiempos(user=user, text=txt2)
        return dedent('''
            No he entendido el mensaje, ¿estas usando mensajes encriptados (OMEMO, OpenPGP, etc)?
            Por favor, desactiva el encriptado y escribe hola para ver las opciones.
        ''').strip()

    def command_error(self, e, *args, user, **kwargs):
        if user == self.config['admin']:
            return str(e) + "\n\n" + traceback.format_exc()
        return dedent('''
            Ha ocurrido un error inesperado. Por favor, vuelva a intentarlo más tarde.
            Si el error persiste deje un issue en https://github.com/s-nt-s/XmppBus/issues
        ''').strip()


if __name__ == '__main__':
    xmpp = BusBot("config.yml")
    xmpp.run()
