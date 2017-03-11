#!/usr/bin/env python
# -*- coding: utf-8 -*-

from basebot import botcmd, XmppBot
from datos import tiempos
from datos import pt
import db
import yaml
import textwrap


class BusBot(XmppBot):

    def format_message(self, txt):
        return "<span style='font-family: monospace'>" + txt.replace("\n", "<br/>") + "</span>"

    def parse_message(self, user, txt):
        words = txt.split(" ")
        if not words[0].isdigit():
            return db.get(user, words[0].lower())
        return txt

    def reply_message(self, user, txt):
        reply = None
        alias = None
        words = txt.split(" ")

        r = tiempos([words[0]])
        linea = words[1] if len(words) > 1 else None
        alias = words[2] if len(words) > 2 else None
        if not r or len(r) == 0:
            msg.reply(
                "Actualmente no hay datos para la parada " + words[0]).send()
            if not alias and linea and not linea.isdigit():
                alias = linea
        else:
            if not alias and linea:
                buses = [i["linea"] for i in r]
                if linea not in buses:
                    alias = linea
                    linea = None
            if linea:
                r = [i for i in r if i["linea"] == linea]

            reply = pt(r)

        if alias:
            txt = " ".join(words[:-1])
            db.set(user, alias.lower(), txt)
        db.set(user, ".", txt)

        return reply

    @botcmd
    def hola(self, user, txt):
        return textwrap.dedent('''
        ¡Hola!
        Escribe el número de una parada para consultar los autobuses que pasan por ella (ej: 435).
        Si quieres ver solo un autobús, añade a continuación dicho bus (ej: 435 51).
        Si quieres repetir la última consulta que hayas hecho escribe simplemente un punto (.).
        Si quieres guardar un marcador a tu consulta añade una palabra tras ella (ej: 435 51 casa) y cuando escribas esa palabra se realizara la consulta guardada.
        Si no te acuerdas de tus marcadores guardados, escribe # y te los listare.
        ''').strip()

    @botcmd(name="#")
    def marcadores(self, user, txt):
        alias = db.get_alias(user)
        if not alias or len(alias) == 0:
            return "Aún no has guardado ningún marcador"
        r = "Estos son tus marcadores:"
        for i in alias:
            r = (r + "\n" + i[0] + ": " + i[1])
        return r

if __name__ == '__main__':
    xmpp = BusBot("config.yml")
    xmpp.run()
