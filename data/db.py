import sqlite3
import os

path = os.path.dirname(os.path.abspath(__file__))

db_user = path + "/db/user.db"
db_data = path + "/db/data.db"


def get_marcador(user, marcador):
    con = sqlite3.connect(db_user)
    c = con.cursor()
    c.execute("select cmd from marcadores where user=? and marcador=?", (user, marcador))
    r = c.fetchone()
    c.close()
    con.close()
    if r and len(r) > 0:
        return r[0]
    return None


def set_marcador(user, marcador, cmd):
    con = sqlite3.connect(db_user)
    c = con.cursor()
    c.execute(
        "insert or replace into marcadores (user, marcador, cmd) values (?, ?, ?)", (user, marcador, cmd))
    c.close()
    con.commit()
    con.close()


def get_marcadores(user):
    con = sqlite3.connect(db_user)
    c = con.cursor()
    c.execute(
        "select marcador, cmd from marcadores where user=? and marcador not like '.%'", (user,))
    r = c.fetchall()
    c.close()
    con.close()
    return r

def del_marcador(user, marcador):
    #args = [user] + marcador
    con = sqlite3.connect(db_user)
    c = con.cursor()
    c.execute("delete from marcadores where user=? and marcador=?" , (user, marcador))
    #c.execute("delete from marcador where user=? and marcador in (%s)" % ','.join('?'*len(marcador)) , args)
    c.close()
    con.commit()
    con.close()

def get_linea(cod, red=None):
    con = sqlite3.connect(db_data)
    c = con.cursor()
    if red:
        c.execute("select id, red, municipio, cod from lineas where id=? and red=?", (cod, red))
    else:
        c.execute("select id, red, municipio, cod from lineas where cod=?", (cod, ))
    r = c.fetchall()
    c.close()
    con.close()
    return r

def get_id_itinerario(red, linea, sentido=1, sublinea=None):
    con = sqlite3.connect(db_data)
    c = con.cursor()
    if sublinea:
        c.execute("select id, sublinea from ids_itinerarios where red=? and linea=? and sentido=? and sublinea=? order by sublinea", (red, linea, sentido, sublinea))
    else:
        c.execute("select id, sublinea from ids_itinerarios where red=? and linea=? and sentido=? order by sublinea", (red, linea, sentido))
    r = c.fetchall()
    c.close()
    con.close()
    return r

def get_itinerario(red, itinerario, sentido=1):
    con = sqlite3.connect(db_data)
    c = con.cursor()
    c.execute("select estaciones.cod, direccion, municipio, denominacion, cp from itinerarios join estaciones on itinerarios.estacion=estaciones.id and itinerarios.red=estaciones.red where itinerarios.red=? and itinerario=? and sentido=? order by orden", (red, itinerario, sentido))
    r = c.fetchall()
    c.close()
    con.close()
    return r

def get_itinerario_mixto(red, linea, sentido=1):
    con = sqlite3.connect(db_data)
    c = con.cursor()
    c.execute("select estaciones.cod, direccion, municipio, denominacion, cp variantes from itinerarios join estaciones on itinerarios.estacion=estaciones.id and itinerarios.red=estaciones.red where itinerarios.red=? and linea=? and sentido=? order by orden", (red, linea, sentido))
    r = c.fetchall()
    c.close()
    con.close()
    visto=[]
    for i in range(len(r)-1,-1,-1):
        e=r[i][0]
        if e in visto:
            del r[i]
        else:
            visto.append(e)
    return r

def get_direccion(estacion):
    con = sqlite3.connect(db_data)
    c = con.cursor()
    c.execute("select distinct direccion from estaciones where cod=?", (estacion,))
    r = c.fetchall()
    c.close()
    con.close()
    if len(r)!=1:
        return None
    return r[0][0]


if __name__ == "__main__":
    con = sqlite3.connect(db_user)
    with open(path + '/schema/user.sql', 'r') as schema:
        c = con.cursor()
        qry = schema.read()
        c.executescript(qry)
        con.commit()
        c.close()
    con.close()
