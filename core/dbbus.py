from os.path import dirname, join, realpath
from munch import Munch

from .dblite import DBLite
from .dblite import dict_factory

ROOT = join(dirname(realpath(__file__)), '../')


def munch_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return Munch.fromDict(d)


class DBBus:
    USER = ROOT + "sql/db/user.db"
    DATA = ROOT + "sql/db/data.db"

    def __init__(self):
        with DBLite(DBBus.USER) as db:
            if len(db.tables) == 0:
                db.execute(ROOT + "sql/schema/user.sql")
        with DBLite(DBBus.DATA) as db:
            if len(db.tables) == 0:
                db.execute(ROOT + "sql/schema/data.sql")

    def get_tarjeta(self, user):
        with DBLite(DBBus.USER, readonly=True) as db:
            return db.one("select tarjeta from tarjetas where user=?", user)

    def set_tarjeta(self, user, tarjeta):
        with DBLite(DBBus.USER) as db:
            db.insert("tarjetas", user=user,
                      tarjeta=tarjeta, insert_or="replace")

    def get_marcador(self, user, marcador):
        with DBLite(DBBus.USER, readonly=True) as db:
            return db.one("select cmd from marcadores where user=? and marcador=?", user, marcador)

    def set_marcador(self, user, marcador, cmd):
        with DBLite(DBBus.USER) as db:
            db.insert("marcadores", user=user, marcador=marcador,
                      cmd=cmd, insert_or="replace")

    def get_marcadores(self, user):
        with DBLite(DBBus.USER, readonly=True) as db:
            r = db.to_list(
                "select marcador, cmd linea, '' buses from marcadores where user=? and marcador not like '.%'", user,
                row_factory=munch_factory)
        for v in r:
            spl = v.linea.split(None, 1)
            if len(spl) > 1:
                v.linea, v.buses = spl
        return r

    def del_marcador(self, user, marcador):
        with DBLite(DBBus.USER) as db:
            db.execute(
                "delete from marcadores where user=? and marcador=?", user, marcador)

    def get_linea(self, cod, red=None):
        with DBLite(DBBus.DATA, readonly=True) as db:
            if red:
                return db.to_list("select id, red, municipio, cod from lineas where id=? and red=?", cod, red,
                                  row_factory=munch_factory)
            return db.to_list("select id, red, municipio, cod from lineas where cod=?", cod, row_factory=munch_factory)

    def get_id_itinerario(self, red, linea, sentido=1, sublinea=None):
        with DBLite(DBBus.DATA, readonly=True) as db:
            if sublinea:
                return db.to_list(
                    "select id, sublinea from ids_itinerarios where red=? and linea=? and sentido=? and sublinea=? order by sublinea",
                    red, linea, sentido, sublinea)
            return db.to_list(
                "select id, sublinea from ids_itinerarios where red=? and linea=? and sentido=? order by sublinea", red,
                linea, sentido)

    def get_itinerario(self, red, itinerario, sentido=1):
        with DBLite(DBBus.DATA, readonly=True) as db:
            return db.to_list(
                "select estaciones.cod estacion, direccion, municipio, denominacion, cp from itinerarios join estaciones on itinerarios.estacion=estaciones.id and itinerarios.red=estaciones.red where itinerarios.red=? and itinerario=? and sentido=? order by orden",
                red, itinerario, sentido, row_factory=munch_factory)

    def get_itinerario_mixto(self, red, linea, sentido=1):
        with DBLite(DBBus.DATA, readonly=True) as db:
            r = db.to_list(
                "select estaciones.cod estacion, direccion, municipio, denominacion, cp variantes from itinerarios join estaciones on itinerarios.estacion=estaciones.id and itinerarios.red=estaciones.red where itinerarios.red=? and linea=? and sentido=? order by orden",
                red, linea, sentido, row_factory=munch_factory)

        visto = []
        for i in range(len(r) - 1, -1, -1):
            e = r[i].estacion
            if e in visto:
                del r[i]
            else:
                visto.append(e)
        return r

    def get_direccion(self, estacion):
        with DBLite(DBBus.DATA, readonly=True) as db:
            return db.one("select distinct direccion from estaciones where cod=?", estacion)
