import inspect
import re
import sys
from datetime import datetime
from io import StringIO

from munch import Munch

from .api import Api
from .dbbus import DBBus
from .util import tmap, yjoin

db = DBBus()

re_rtrim = re.compile(r"^\s*\n")
re_sp = re.compile(r"\s+")
red_linea_sub = re.compile(
    "^(?:([689])_)?([\dA-Z]+)(?:-(\d+))?$", re.IGNORECASE)

PRNT = Munch(
    func=print,
    line=""
)


def print(*args, **kvargs):
    # Previene imprimir dos lineas vacias seguidas
    io_line = StringIO()
    PRNT.func(*args, file=io_line, flush=True, **kvargs)
    line = io_line.getvalue()
    line = line.strip()
    if tmap(len, (line, PRNT.line)) == (0, 0):
        return
    PRNT.line = line
    PRNT.func(*args, **kvargs)


def print_dict(kv, prefix=""):
    max_campo = max(len(i[0]) for i in kv.items())
    line = "%-" + str(max_campo) + "s:"
    for k, v in kv.items():
        if v:
            print(prefix + (line % k), end="")
            if isinstance(v, (tuple, list, set)):
                v = ", ".join(str(i) for i in v)
            if isinstance(v, dict):
                print("")
                print_dict(v, prefix="  ")
            else:
                print(" " + str(v))


def get_width(arr):
    keys = set()
    for a in arr:
        keys = keys.union(a.keys())
    wdth = {k: 0 for k in keys}
    for a in arr:
        for k, v in list(wdth.items()):
            if a.get(k) is not None:
                wdth[k] = max(v, len(str(a[k])))
    return Munch.fromDict(wdth)



def parse_route_name(s):
    if s is None:
        return s
    s = s.strip()
    if len(s) == 0:
        return s
    x = re.sub(r"(\([^\)\(]+(\)|$))",
               lambda x: x.group().replace(" ", "$%$"), s)
    x = x.split(" - ")[-1]
    x = x.replace("$%$", " ")
    return x


class Printer:
    IMG_CARD = "https://www.tarjetatransportepublico.es/CRTM-ABONOS/archivos/img/TTP.jpg"

    def __init__(self):
        PRNT.line = ""

    def times(self, id, *lines, maxwait=99):
        id = str(id)
        lines = tuple(str(l) for l in lines)
        d = Api().get_times(id)
        if d.get('error') is True:
            print("La parada {} no existe".format(id))
            return
        now = datetime.utcnow()
        routes = []
        for r in d.routes:
            if len(lines) and r.lineCode not in lines:
                continue
            for t in r.times:
                minutes = round((t.arrivalDate - now).total_seconds() / 60)
                if maxwait is not None and minutes > maxwait:
                    continue
                routes.append(Munch(
                    code=r.lineCode,
                    destiny=parse_route_name(r.routeName),
                    min=minutes
                ))
        strstop = str(id)
        direcci = db.get_direccion(strstop) or d.get('stopName')
        if direcci not in (None, ''):
            strstop = strstop + ' (' + direcci + ')'
        routes = sorted(routes, key=lambda x: (x.min, int(x.code) if x.code.isdigit() else 99999999, x.code))
        if len(routes) == 0:
            if len(lines) == 0:
                print("La parada {} actualmente no tiene ninguna ruta".format(strstop))
            else:
                print("No hay datos para {} en la parada {}".format(
                    yjoin(lines, singular='el bus', plural='los buses'),
                    strstop
                ))
            return
        if len(lines) == 0:
            print("Los tiempos en la parada {} son:".format(strstop))
        else:
            print("Los tiempos en la parada {} para {} son:".format(
                strstop, yjoin(lines, singular='el bus', plural='los buses')
            ))
        wdt = get_width(routes)
        fln = "{min:>%s} min {code:>%s} -> {destiny}" % (
            max(2, wdt.min), wdt.code)
        for r in routes:
            print(fln.format(**r))

    def _card(self, card):
        d = Api().get_card(card)
        if d.get('error') is True:
            print("No hay datos para la tarjeta {}".format(card))
            print("¿Seguro que ha introducido bien el número? Fijese en el ejemplo:")
            print(Printer.IMG_CARD)
            return
        tickets = []
        for t in d.tickets:
            expires = tuple(v.lastUseDate for k, v in t.items()
                            if isinstance(v, dict) and v.get('lastUseDate'))
            tickets.append(Munch(
                name=t.name,
                expires=max(expires) if len(expires) > 0 else None
            ))
        if len(tickets) == 0:
            if d.isActive:
                print("La tarjeta {} esta ACTIVA pero no contiene ningún ticket".format(card))
            else:
                print("La tarjeta {} esta INACTIVA y no contiene ningún ticket".format(card))
            return
        if len(tickets) == 1:
            t = tickets[0]
            if d.isActive:
                print("La tarjeta {} ({}) esta ACTIVA".format(card, t.name), end="")
                if t.expires is not None:
                    print(" hasta {:%Y-%m-%d}".format(t.expires), end="")
                print("")
            else:
                print("La tarjeta {} ({}) esta INACTIVA".format(card, t.name), end="")
                if t.expires is not None:
                    print(" (caducada en {:%Y-%m-%d})".format(t.expires), end="")
                print("")
            return
        if d.isActive:
            print("la tarjeta {} esta ACTIVA".format(card))
        else:
            print("la tarjeta {} esta INACTIVA".format(card))
        wdt = get_width(tickets)
        fln = "{:>%s}" % (max(2, wdt.name),)
        for t in tickets:
            print(fln.format(t.name), end="")
            if t.expires:
                print(" {:%Y-%m-%d}".format(t.expires), end="")
            print("")

    def card(self, *args, **kvargs):
        self._card(*args, **kvargs)
        print("\n(*) Función beta, puede dar datos erroneos o tardar en actualizar")

    def _paradas(self, linea, *args):
        linea = str(linea).upper()
        m = red_linea_sub.match(linea)
        if not m:
            print(linea + " no cumple el formato de línea")
            return

        rd, li, su = m.groups()
        sent = 2 if len(args) > 0 and args[0] == "+" else 1

        idlineas = db.get_linea_con_itinerario(li, rd)
        if len(idlineas) == 0:
            print("No hay datos para la linea " + linea)
            return
        if len(idlineas) > 1:
            print("Exiten varias líneas {}, por favor, concreta escribiendo:".format(li))
            for lin in idlineas:
                print("{red}_{id} para la linea de {municipios}".format(**lin))
            return

        lin = idlineas[0]

        itinerario = db.get_itinerario_mixto(lin.red, lin.id, sent)

        if len(itinerario) == 0:
            print("No hay datos para la línea " + linea)
            return

        variantes = len(db.get_id_itinerario(lin.red, lin.id, sent, su))
        reply = "Itinerario "
        if variantes > 1:
            reply = reply + "(aproximado) "

        reply = reply + "de la línea " + lin.cod
        if lin.cod != linea:
            reply = reply + " de " + lin.municipio + " (" + linea + ")"
        print(reply + ':\n')

        wdt = get_width(itinerario)
        fln = "{estacion:>%s} {direccion}" % wdt.estacion
        for parada in itinerario:
            print(fln.format(**parada))

        if sent == 1 or variantes > 1:
            print("")
        if sent == 1:
            print("Para ver el sentido contrario escribe: paradas %s +" % linea)
        if variantes > 1:
            print("Antes de desplazarte consulta tu parada para confirmar que el bus va a pasar por ella")

    def paradas(self, *args, **kvargs):
        self._paradas(*args, **kvargs)
        print("\n(*) Función beta, puede dar datos erroneos o desactualizados")

    def marcadores(self, user):
        marcadores = db.get_marcadores(user)
        if len(marcadores) == 0:
            print("Aún no has guardado ningún marcador")
            return
        #wdt = get_width(marcadores)
        #fln = "{marcador:<%s} {linea:>%s} {buses}" % (wdt.marcador, wdt.linea)
        fln = "{marcador}: {linea} {buses}"
        print("Estos son tus marcadores:\n")
        for m in marcadores:
            print(fln.format(**m).rstrip())
        print("")
        print("Si quieres eliminar alguno, escribe borrar seguido del nombre del marcador.")


def print_to_str(fnc):
    def fnc_wrapper(*args, **kvargs):
        old_stdout = sys.stdout
        result = StringIO()
        sys.stdout = result
        fnc(*args, **kvargs)
        sys.stdout = old_stdout
        result_string = result.getvalue()
        result_string = result_string.rstrip()
        return result_string

    return fnc_wrapper


def for_all_methods(decorator):
    def decorate(cls):
        for name, fn in inspect.getmembers(cls, inspect.isfunction):
            if not name.startswith("_"):
                setattr(cls, name, decorator(fn))
        return cls

    return decorate


@for_all_methods(print_to_str)
class StrPrinter(Printer):
    pass


if __name__ == "__main__":
    p = Printer()
    p.paradas(sys.argv[1])
