#!/usr/bin/env python
# -*- coding: utf-8 -*-

from basebot import botcmd, XmppBot
from datos import tiempos
from datos import pt
import db
import yaml
import os
import textwrap


class BusBot(XmppBot):

    def format_message(self, txt):
        return "<span style='font-family: monospace'>" + txt.replace("\n", "<br/>") + "</span>"

    def parse_message(self, user, txt):
        word1 = txt.split(" ")[0]
        if word1.isdigit():
            return txt
        return db.get(user, txt.lower()) #word1.lower())

    def reply_message(self, user, txt):
        reply = None
        alias = None
        words = txt.split(" ")

        r = tiempos([words[0]])

        linea = words[1] if len(words) > 1 else None
        alias = " ".join(words[2:]) if len(words) > 2 else None

        if not r or len(r) == 0:
            reply = "Actualmente no hay datos para la parada " + words[0]
            if linea and not linea.isdigit():
                alias = " ".join(words[1:])
        else:
            if linea:
                buses = [i["linea"] for i in r]
                if linea not in buses:
                    alias = " ".join(words[1:])
                    linea = None
            if linea:
                r = [i for i in r if i["linea"] == linea]

            reply = pt(r)

        if alias:
            index = 2 if linea else 1
            txt = " ".join(words[0:index])
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
        r = r + "\nSi quieres eliminar alguno, escribe borrar seguido del nombre del marcador."
        return r

    @botcmd(name="borrar")
    def borrar_marcador(self, user, txt):
        alias=" ".join(txt.split(' ')[1:]).lower()
        if len(alias)==0:
            return "¿Qué marcador quieres borrar? Escribelo despues de la palabra borrar."
        db.rem_alias(user, alias)
        return "¡Marcadores borrados!"

if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(path)
    xmpp = BusBot("config.yml")
    xmpp.run()
