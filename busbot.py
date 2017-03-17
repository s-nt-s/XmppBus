#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xmppbot import botcmd, XmppBot
from datos import tiempos
from datos import pt
import db
import yaml
import os
import textwrap
import re
import os
import sys
'''
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
'''
puntos = re.compile(r"^\.+$")
historia = 3

class BusBot(XmppBot):

    def format_message(self, txt):
        return "<span style='font-family: monospace'>" + txt.replace("\n", "<br/>") + "</span>"

    @botcmd(regex=re.compile(r"(hola|\?$)", re.IGNORECASE), rg_mode="search")
    def hola(self, user, txt, args):
        return textwrap.dedent('''
        ¡Hola!
        Escribe el número de una parada para consultar los autobuses que pasan por ella (ej: 435).
        Si quieres ver solo un autobús, añade a continuación dicho bus (ej: 435 51).
        Si quieres repetir la última consulta que hayas hecho escribe simplemente un punto (.).
        Si quieres guardar un marcador a tu consulta añade una palabra tras ella (ej: 435 51 casa) y cuando escribas esa palabra se realizara la consulta guardada.
        Si no te acuerdas de tus marcadores guardados, escribe # y te los listare.
        ''').strip()

    @botcmd(regex=re.compile(r"^(\d+.*)"), rg_mode="match")
    def reply_message(self, user, txt, args):
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

        if args is None or len(args)==0 or not puntos.match(args[0]):
            for h in range(historia-1, 0, -1):
                hs = db.get(user, "." * h)
                if hs:
                     db.set(user, "." * (h+1), hs)

            db.set(user, ".", txt)
        if not r or len(r) == 0:
            return reply
        a = txt.split(" ")
        if len(a)>1:
            tit = "Los tiempos del bus %s en la parada %s son:\n" % (a[1], a[0])
        else:
            tit = "Los tiempos en la parada %s son:\n" % a[0]

        return tit + reply

    @botcmd(regex=re.compile(r"^(\D+.*)$"), rg_mode="match")
    def reply_else(self, user, txt, args):
        word1 = txt.split(" ")[0]
        txt2 = db.get(user, txt.lower())
        if txt2:
            return self.reply_message(user, txt2, [txt])
        return None

    @botcmd(name="paradas")
    def reply_paradas(self, user, txt, args):
        l=args[0]
        s= 2 if args[-1]=="+" else 1
        txt="data/txt/" + str(s) + "/" + l.upper() + ".txt"
        if not os.path.isfile(txt):
            return "No se encuentran las paradas de la línea "+l
        with open(txt, 'r') as myfile:
            data=myfile.read().rstrip()
            reply = "Itinerario (aproximado) de la línea "+l+":\n" + data
        if s == 1:
            reply = reply + ("\n\nPara ver el sentido contrario escribe: paradas %s +" % l)
        reply = reply + "\n\nAntes de desplazarte, consulta los datos de la parada a la que pretendes ir para confirmar que tu bus pasa por ahí."
        reply = reply + "\nPor ejemplo: "+data.strip().split(" ")[0]+" "+l
        return reply

    @botcmd(name="#")
    def marcadores(self, user, txt, args):
        alias = db.get_alias(user)
        if not alias or len(alias) == 0:
            return "Aún no has guardado ningún marcador"
        r = "Estos son tus marcadores:"
        for i in alias:
            r = (r + "\n" + i[0] + ": " + i[1])
        r = r + "\nSi quieres eliminar alguno, escribe borrar seguido del nombre del marcador."
        return r

    @botcmd(name="borrar")
    def borrar_marcador(self, user, txt, args):
        alias=" ".join(txt.split(' ')[1:]).lower()
        if len(alias)==0:
            return "¿Qué marcador quieres borrar? Escribelo despues de la palabra borrar."
        db.rem_alias(user, alias)
        return "¡Marcador borrado!"

if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(path)
    xmpp = BusBot("config.yml")
    xmpp.run()
