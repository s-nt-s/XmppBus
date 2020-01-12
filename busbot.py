#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import textwrap
import traceback

import yaml
from xmppbot import XmppBot, botcmd

from data import db
from data.datos import pt, get_tiempos, get_saldo

puntos = re.compile(r"^\.+$")
red_linea_sub =re.compile("^(?:([689])_)?([\dA-Z]+)(?:-(\d+))?$", re.IGNORECASE)
historia = 3
img_tarjeta="https://www.tarjetatransportepublico.es/CRTM-ABONOS/archivos/img/TTP.jpg"

class BusBot(XmppBot):

    def tune_reply(self, txt):
        return "```\n%s\n```" % txt

    @botcmd(regex=re.compile(r"(hola|\?$)", re.IGNORECASE), rg_mode="search")
    def hola(self, *args, **kwargs):
        return textwrap.dedent('''
        ¡Hola!
        Escribe el número de una parada para consultar los autobuses que pasan por ella (ej: 435).
        Si quieres ver solo un autobús, añade a continuación dicho bus (ej: 435 51).
        Si quieres repetir la última consulta que hayas hecho escribe simplemente un punto (.).
        Si quieres guardar un marcador a tu consulta añade una palabra que empieze por # tras ella (ej: 435 51 #casa) y cuando escribas esa palabra se realizara la consulta guardada.
        Si no te acuerdas de tus marcadores guardados, escribe # y te los listare.
        También puedes consultar el itinerario de una línea escribiendo la palabra paradas seguida del número de linea (ej: paradas 51),
        o consultar el saldo de tu tarjeta de transporte escribiendo saldo.
        ''').strip()


    @botcmd(regex=re.compile(r"^saldo(\s+[\d\s]+)?$", re.IGNORECASE), rg_mode="match")
    def saldo(self, tarjeta, *args, user, **kwargs):
        if not tarjeta:
            tarjeta = ""
        tarjeta = re.sub(r"\s+", "", tarjeta)
        from_db = False
        if len(tarjeta)==0:
            tarjeta = db.get_tarjeta(user)
            from_db = True
            if tarjeta is None:
                return "Escriba el número de su tarjeta ( " + img_tarjeta + " ) después de la palabra saldo"
        elif len(tarjeta)!=13 or not tarjeta.isdigit():
            return tarjeta + " no es un número de tarjeta válido ( " + img_tarjeta + " )"
        saldo = get_saldo(tarjeta)
        if not saldo:
            return tarjeta + " no es un número de tarjeta válido ( " + img_tarjeta + " )"
        if not from_db:
            db.set_tarjeta(user, tarjeta)
        return "Información para la tarjeta "+tarjeta+":\n\n"+saldo

    @botcmd(name="paradas")
    def reply_paradas(self, linea, *args, user, **kwargs):
        linea=linea.upper()
        m=red_linea_sub.match(linea)
        if not m:
            return linea + " no cumple el formato de línea"

        rd, li, su = m.groups()
        sent= 2 if len(args)>0 and args[0]=="+" else 1

        idlineas=db.get_linea(li,rd)
        if len(idlineas)==0:
            return "No hay datos para la linea "+linea
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
            return "No hay datos para la linea "+linea
        elif len(iditinerarios)>1:
            reply = "La línea "+linea+" tiene varios itinerarios, por favor, concreta escribiendo:"
            for iditinerario in iditinerarios:
                su=iditinerario[1]
                reply = reply +"\n"+linea+"-"+su+" para el subitinerario "+su
            return reply

        iditinerario, su, plong = iditinerarios[0]

        itinerario = db.get_itinerario(rd, iditinerario, sent)
        '''

        itinerario = db.get_itinerario_mixto(rd, li, sent)

        if len(itinerario)==0:
            return "No hay datos para la línea "+linea

        reply = "Itinerario "
        if variantes>1:
            reply = reply + "(aproximado) "

        reply = reply + "de la línea "+cod
        if cod!=linea:
            reply = reply + " de " + muni +" ("+linea+")"
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
            reply = reply + ("\nPara ver el sentido contrario escribe: paradas %s +" % linea)
        if variantes>1:
            reply = reply + ("\nAntes de desplazarte consulta tu parada para confirmar que el bus va a pasar por ella")
        return reply

    @botcmd(name="#")
    def marcadores(self, *args, user, **kwargs):
        marcador = db.get_marcadores(user)
        if not marcador or len(marcador) == 0:
            return "Aún no has guardado ningún marcador"
        r = "Estos son tus marcadores:"
        for i in marcador:
            r = (r + "\n" + i[0] + ": " + i[1])
        r = r + "\nSi quieres eliminar alguno, escribe borrar seguido del nombre del marcador."
        return r

    @botcmd(name="borrar")
    def borrar_marcador(self, *marcador, user, **kwargs):
        if len(marcador)==0:
            return "¿Qué marcador quieres borrar? Escribelo despues de la palabra borrar."
        marcador=" ".join(marcador).lower()
        db.del_marcador(user, marcador)
        return "¡Marcador borrado!"

    @botcmd(regex=re.compile(r"^(\d+.*)"), rg_mode="match")
    def reply_tiempos(self, *args, user, text, **kwargs):
        reply = None
        slp = text.split("#", 1)
        marcador = slp[-1] if len(slp)>1 else None
        words = slp[0].split(" ")
        parada = words[0]
        lineas = sorted(set(words[1:]))

        r = get_tiempos([parada])

        if not r or len(r) == 0:
            reply = "Actualmente no hay datos para la parada " + parada
        elif lineas:
            r = [i for i in r if i["linea"] in lineas]
            if len(r)==0:
                reply = "Actualmente no hay datos para la parada " + parada+ ": " + ", ".join(lineas)

        if r:
            reply = pt(r)

        if marcador:
            db.set_marcador(user, marcador.lower(), parada + " " + " ".join(lineas))

        if args is None or len(args)==0 or not puntos.match(args[0]):
            for h in range(historia-1, 0, -1):
                hs = db.get_marcador(user, "." * h)
                if hs:
                     db.set_marcador(user, "." * (h+1), hs)

            db.set_marcador(user, ".", text)
        if not r or len(r) == 0:
            return reply
        d = db.get_direccion(parada)
        if d:
            parada += " ("+d+")"
        if len(lineas)==1:
            tit = "Los tiempos del bus %s en la parada %s son:\n" % (lineas[0], parada)
        elif len(lineas)>1:
            tit = "Los tiempos de los buses %s y %s en la parada %s son:\n" % (", ".join(lineas[:-1]), lineas[-1], parada)
        else:
            tit = "Los tiempos en la parada %s son:\n" % parada

        return tit + reply

    @botcmd(regex=re.compile(r"^(\D+.*)$"), rg_mode="match")
    def reply_else(self, *args, user, text, **kwargs):
        marcador = text.lower()
        txt2 = db.get_marcador(user, marcador)
        if not txt2 and marcador.startswith("#"):
            txt2 = db.get_marcador(user, marcador[1:])
        if txt2:
            return self.reply_tiempos(user=user, text=txt2)
        return None

    def command_error(self, e, *args, user, **kwargs):
        if user == self.config['admin']:
            return str(e)+"\n\n"+traceback.format_exc()
        return "Ha ocurrido un error inesperado. Por favor, vuelva a intentarlo más tarde."

if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(path)
    xmpp = BusBot("config.yml")
    xmpp.run()
