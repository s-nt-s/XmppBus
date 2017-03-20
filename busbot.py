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
red_linea_sub =re.compile("^(?:([689])_)?([\dA-Z]+)(?:-(\d+))?$", re.IGNORECASE)
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
        marcador = None
        words = txt.split(" ")

        r = tiempos([words[0]])

        linea = words[1] if len(words) > 1 else None
        marcador = " ".join(words[2:]) if len(words) > 2 else None

        if not r or len(r) == 0:
            reply = "Actualmente no hay datos para la parada " + words[0]
            if linea and not linea.isdigit():
                marcador = " ".join(words[1:])
        else:
            if linea:
                buses = [i["linea"] for i in r]
                if linea not in buses:
                    marcador = " ".join(words[1:])
                    linea = None
            if linea:
                r = [i for i in r if i["linea"] == linea]

            reply = pt(r)

        if marcador:
            index = 2 if linea else 1
            txt = " ".join(words[0:index])
            db.set_marcador(user, marcador.lower(), txt)

        if args is None or len(args)==0 or not puntos.match(args[0]):
            for h in range(historia-1, 0, -1):
                hs = db.get_marcador(user, "." * h)
                if hs:
                     db.set_marcador(user, "." * (h+1), hs)

            db.set_marcador(user, ".", txt)
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
        txt2 = db.get_marcador(user, txt.lower())
        if txt2:
            return self.reply_message(user, txt2, [txt])
        return None

    @botcmd(name="paradas")
    def reply_paradas(self, user, txt, args):
        arg=args[0]
        m=red_linea_sub.match(arg)
        if not m:
            return arg + " no cumple el formato de línea"
        rd, li, su = m.groups()
        sent= 2 if args[-1]=="+" else 1


        idlineas=db.get_linea(li,rd)
        if len(idlineas)==0:
            return "No hay datos para la linea "+arg
        elif len(idlineas)>1:
            reply = "Exiten varias líneas "+li+", por favor, concreta escribiendo:"
            for idlinea in idlineas:
                li=str(idlinea[0])
                rd=str(idlinea[1])
                reply = reply + "\n" + rd+"_"+li+" para la línea de "+idlinea[2]
                
            return reply

        li, rd, muni, cod = idlineas[0]

        iditinerarios=db.get_id_itinerario(rd, li, sent, su)
        variantes=len(iditinerarios)
        
        '''
        if len(iditinerarios)==0:
            return "No hay datos para la linea "+arg
        elif len(iditinerarios)>1:
            reply = "La línea "+arg+" tiene varios itinerarios, por favor, concreta escribiendo:"
            for iditinerario in iditinerarios:
                su=iditinerario[1]
                reply = reply +"\n"+arg+"-"+su+" para el subitinerario "+su
            return reply
        
        iditinerario, su, plong = iditinerarios[0]
        
        itinerario = db.get_itinerario(rd, iditinerario, sent)
        '''

        itinerario = db.get_itinerario_mixto(rd, li, sent)
        
        if len(itinerario)==0:
            return "No hay datos para la línea "+arg

        reply = "Itinerario "
        if variantes>1:
            reply = reply + "(aproximado) "

        reply = reply + "de la línea "+cod
        if cod!=arg:
            reply = reply + " de " + muni +" ("+arg+")"
        reply = reply + ":\n"

        reply_itinerario=""
        for item in itinerario:
            dire=item[3]
            '''
            if not muni:
                dire=dire+", "+item[2]
            '''
            reply_itinerario = reply_itinerario + ("%5s %s" % (item[0], dire)) + "\n"

        reply_itinerario = textwrap.dedent(reply_itinerario.rstrip())

        reply = reply + "\n" + reply_itinerario
        
        if sent == 1 or variantes>1:
            reply = reply + "\n"
        if sent == 1:
            reply = reply + ("\nPara ver el sentido contrario escribe: paradas %s +" % arg)
        if variantes>1:
            reply = reply + ("\nAntes de desplazarte consulta tu parada para confirmar que el bus va a pasar por ella")
        return reply

    @botcmd(name="#")
    def marcadores(self, user, txt, args):
        marcador = db.get_marcadores(user)
        if not marcador or len(marcador) == 0:
            return "Aún no has guardado ningún marcador"
        r = "Estos son tus marcadores:"
        for i in marcador:
            r = (r + "\n" + i[0] + ": " + i[1])
        r = r + "\nSi quieres eliminar alguno, escribe borrar seguido del nombre del marcador."
        return r

    @botcmd(name="borrar")
    def borrar_marcador(self, user, txt, args):
        marcador=" ".join(txt.split(' ')[1:]).lower()
        if len(marcador)==0:
            return "¿Qué marcador quieres borrar? Escribelo despues de la palabra borrar."
        db.del_marcadores(user, marcador)
        return "¡Marcador borrado!"

if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(path)
    xmpp = BusBot("config.yml")
    xmpp.run()
