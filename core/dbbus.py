from os.path import dirname, join, realpath
from munch import Munch

from .dblite import DBLite
from datetime import datetime

ROOT = join(dirname(realpath(__file__)), '../')


def munch_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    for dt_field in ("caducado", "consultado"):
        val = d.get(dt_field)
        if val is not None:
            d[dt_field] = datetime.strptime(d[dt_field], "%Y-%m-%d").date()
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

    def get_tarjetas(self):
        with DBLite(DBBus.USER, readonly=True) as db:
            return db.to_list("select * from tarjetas", row_factory=munch_factory)
        
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

    def get_linea_con_itinerario(self, cod, red=None):
        with DBLite(DBBus.DATA, readonly=True) as db:
            sql = '''
                select distinct
                    l.red,
                    l.id,
                    l.cod,
                    l.denominacion
                from
                    linea l join itinerario i on
                        l.red = i.red and
                        l.id = i.linea
                where
            '''.strip()+' '
            if red:
                return db.to_list(sql+"l.id=? and l.red=?", cod, red,
                                  row_factory=munch_factory)
            return db.to_list(sql+"l.cod=?", cod, row_factory=munch_factory)

    def get_id_itinerario(self, red, linea, sentido=1, sublinea=None):
        with DBLite(DBBus.DATA, readonly=True) as db:
            sql = '''
            select 
                id, 
                sublinea
            from 
                ids_itinerario
            where
                red=? and
                linea=? and
                sentido=? 
            '''.strip()+' '
            if sublinea:
                return db.to_list(sql+"and sublinea=? order by sublinea", red, linea, sentido, sublinea)
            return db.to_list(sql+"order by sublinea", red, linea, sentido)

    def get_itinerario(self, red, itinerario, sentido=1):
        with DBLite(DBBus.DATA, readonly=True) as db:
            return db.to_list('''
                select 
                    e.cod estacion, 
                    e.direccion, 
                    e.municipio, 
                    e.denominacion
                from 
                    itinerario i join estacion e on 
                        i.estacion=e.id and 
                        i.red=e.red
                where 
                    i.red=? and 
                    i.id=? and 
                    i.sentido=? 
                order by orden
                ''',
                red, itinerario, sentido, row_factory=munch_factory)

    def get_itinerario_mixto(self, red, linea, sentido=1):
        with DBLite(DBBus.DATA, readonly=True) as db:
            r = db.to_list('''
                select 
                    e.cod estacion, 
                    e.direccion, 
                    e.municipio, 
                    e.denominacion
                from
                    itinerario i join estacion e on 
                        i.estacion=e.id and 
                        i.red=e.red
                where 
                    i.red=? and 
                    i.linea=? and 
                    i.sentido=?
                order by orden
                ''',
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
            return db.one("select distinct direccion from estacion where cod=?", estacion)
