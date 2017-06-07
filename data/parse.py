#!/usr/bin/python
# -*- coding: utf-8 -*-

import csv
import glob
import locale
import os
import re
import sqlite3
import sys

path = os.path.dirname(os.path.abspath(__file__))

database = path + "/tmp/data.db"

con = sqlite3.connect(database)

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

HEAD_LINEA_ID = 'CODIGOGESTIONLINEA'
HEAD_LINEA_COD = 'NUMEROLINEAUSUARIO'
HEAD_ESTACION_ID = 'CODIGOESTACION'
HEAD_ESTACION_COD = 'CODIGOEMPRESA'
HEAD_SENTIDO = 'SENTIDO'
HEAD_SUBLINEA = 'CODIGOSUBLINEA'
HEAD_ORDEN = 'NUMEROORDEN'
HEAD_DIRECCION = 'DIRECCION'
HEAD_DIRECCION_ALT = ["TIPOVIA", "PARTICULA", "NOMBREVIA", "TIPONUMERO", "NUMEROPORTAL"]
HEAD_MUNICIPIO = 'MUNICIPIO'
HEAD_MUNICIPIO_COD = 'CODIGOMUNICIPIO'
HEAD_PROVINCIA_COD = 'CODIGOPROVINCIA'
HEAD_DENOMINACION = 'DENOMINACION'
HEAD_CODIGOPOSTAL = 'CODIGOPOSTAL'
HEAD_ITINERARIO_ID = 'CODIGOITINERARIO'

sp = re.compile(r"\s+", re.MULTILINE | re.UNICODE)
sn = re.compile(r"( SN *)+$| N S\/N *$", re.UNICODE)
cn = re.compile(r" Nº? (\d+[A-Z]?)$", re.UNICODE)
pr1 = re.compile(r"\( +")
pr2 = re.compile(r" +\)")
el = re.compile(r"^([^,]+), +(El|Las|La) *$", re.UNICODE)
pre = re.compile(r"\b([A-Z]º)", re.UNICODE)
cleanlinea = re.compile(r"[¡]", re.UNICODE)

arti = " (de las|de la|del|de)? *"
subs = [
    re.compile("Calle" + arti, re.UNICODE | re.IGNORECASE),
    "c/ ",
    re.compile("Plaza" + arti, re.UNICODE | re.IGNORECASE),
    "Pl ",
    re.compile("(Avenida|Avda)" + arti, re.UNICODE | re.IGNORECASE),
    "Avda ",
    re.compile("Paseo" + arti, re.UNICODE | re.IGNORECASE),
    "Pº ",
    re.compile("Ronda" + arti, re.UNICODE | re.IGNORECASE),
    "Rda ",
]


redes = ["6", "8", "9"]
iteraciones = 0

def progreso(total):
    global iteraciones
    porcentaje=(iteraciones*100)/total
    if (iteraciones % 10) == 0 or porcentaje==100:
        sys.stdout.write("\r%3d%% de %5d" % (porcentaje, total))
        sys.stdout.flush()
    if iteraciones == total:
        iteraciones=0
    else:
        iteraciones = iteraciones+1

def title(s):
    s = unicode(s).title()
    s = s.replace(" De La ", " de la ")
    s = s.replace(" De Las ", " de las ")
    s = s.replace(" Del ", " del ")
    s = s.replace(" De ", " de ")
    s = s.replace(" Y ", " y ")
    return s


def dire_muni_demo(dire, muni, demo):
    muni = title(muni)
    muni = el.sub(r"\2 \1", muni)
    muni = sp.sub(" ", muni).strip()

    dire = sp.sub(" ", dire).strip()
    dire = sn.sub("", dire)
    dire = cn.sub(r" \1", dire)
    dire = pr1.sub(r"(", dire)
    dire = pr2.sub(r"(", dire)
    dire = title(dire)
    for i in range(0, len(subs), 2):
        dire = subs[i].sub(subs[i + 1], dire)

    demo = demo.replace("-", " - ")
    demo = demo.replace(".", ". ")
    demo = pre.sub(r"\1 ", demo)
    demo = sp.sub(" ", demo).strip()
    demo = sn.sub("", demo)
    demo = cn.sub(r" \1", demo)
    demo = title(demo)

    return dire, muni, demo

def get_direccion(row):
    if HEAD_DIRECCION in row:
        return row[HEAD_DIRECCION]
    dire=""
    for h in HEAD_DIRECCION_ALT:
        dire= dire + " "+row[h]
    return sp.sub(" ",dire).strip()


def get_municipio(row):
    if HEAD_MUNICIPIO in row:
        return row[HEAD_MUNICIPIO]
    cod_prov=row[HEAD_PROVINCIA_COD]
    cod_muni=row[HEAD_MUNICIPIO_COD]
    
    c2 = con.cursor()
    c2.execute("select municipio from municipios where cod_prov=? and cod_muni=?", (cod_prov, cod_muni))
    muni = c2.fetchone()[0]
    c2.close()
    return muni

def rellenar_tablas():
    with open(path + '/schema/data.sql', 'r') as schema:
        c = con.cursor()
        qry = schema.read()
        c.executescript(qry)
        con.commit()
        c.close()
    
    c = con.cursor()

    for _csv in glob.glob("csv/*.csv"):
        print "======== MUNICIPIOS "+_csv
        with open(_csv, 'rb') as csvfile:
            sr = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            total=len(list(sr))-1
            csvfile.seek(0)
            next(sr, None)
            for row in sr:
                progreso(total)
                if HEAD_MUNICIPIO in row and HEAD_MUNICIPIO_COD in row and HEAD_PROVINCIA_COD in row:
                    cod_muni=sp.sub(" ",row[HEAD_MUNICIPIO_COD]).strip()
                    cod_prov=sp.sub(" ",row[HEAD_PROVINCIA_COD]).strip()
                    muni=unicode(sp.sub(" ",row[HEAD_MUNICIPIO]).strip())
                    if cod_prov and cod_muni and muni:
                        c.execute("select count(*) from municipios where cod_prov=? and cod_muni=? and municipio=?", (cod_prov, cod_muni, muni))
                        count = c.fetchone()
                        if count[0]==0:
                            c.execute("insert into municipios (cod_prov, cod_muni, municipio) values (?, ?, ?)", (cod_prov, cod_muni, muni))
        print ""

    c.close()
    con.commit()

    c = con.cursor()
    
    for i in redes:
        print "======== LINEAS "+i
        visto=[]
        sql = "insert into lineas (red, id, cod) values (" + i + ", ?, ?)"
        with open('csv/lineas_' + i + '.csv', 'rb') as csvfile:
            sr = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            total=len(list(sr))-1
            csvfile.seek(0)
            next(sr, None)
            for row in sr:
                progreso(total)
                linea=row[HEAD_LINEA_ID].upper()
                if linea in visto:
                    continue
                visto.append(linea)
                cod=cleanlinea.sub("",row[HEAD_LINEA_COD]).upper()
                c.execute(sql, (linea, cod))
                con.commit()
        c.close()
        c = con.cursor()
        print ""
        print "======== ESTACIONES "+i
        sql = "insert into estaciones (red, id, cod, direccion, municipio, denominacion, cp) values (" + i + ", ?, ?, ?, ?, ?, ?)"
        with open('csv/estaciones_' + i + '.csv', 'rb') as csvfile:
            sr = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            total=len(list(sr))-1
            csvfile.seek(0)
            next(sr, None)
            for row in sr:
                progreso(total)
                a = row[HEAD_ESTACION_ID]
                b = row[HEAD_ESTACION_COD]
                dire, muni, demo = dire_muni_demo(
                    get_direccion(row), get_municipio(row), row[HEAD_DENOMINACION])
                if not b or len(b) == 0:
                    b = a
                c.execute(sql, (a, b, dire, muni, demo, row[HEAD_CODIGOPOSTAL]))
                con.commit()
        print ""

    c.close()
    c = con.cursor()

    for i in redes:
        print "======== ITINERARIOS "+i
        sql = "insert into itinerarios (red, itinerario, sentido, linea, sublinea, estacion, orden) values (" + i + ", ?, ?, ?, ?, ?, ?)"
        with open('csv/itinerario_' + i + '.csv', 'rb') as csvfile:
            sr = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            total=len(list(sr))-1
            csvfile.seek(0)
            next(sr, None)
            for row in sr:
                progreso(total)
                c.execute(sql, (
                          row[HEAD_ITINERARIO_ID],
                          row[HEAD_SENTIDO], 
                          row[HEAD_LINEA_ID].upper(),
                          row[HEAD_SUBLINEA],
                          row[HEAD_ESTACION_ID],
                          row[HEAD_ORDEN]))
                con.commit()
        print ""

    c.close()
    c = con.cursor()

    print "======== IDS_ITINERARIOS"

    c.execute('''INSERT INTO ids_itinerarios (red, id, linea, sublinea, sentido)
                SELECT red, itinerario id, linea, sublinea, sentido
                FROM itinerarios
                group by red, itinerario, linea, sublinea, sentido''')
    con.commit()

    c.close()

def update_tablas():
    print "======== UPDATE LINEAS"

    c = con.cursor()
    c.execute("select red, id from lineas")
    lineas = c.fetchall()
    c.close()

    total=len(lineas)
    for linea in lineas:
        progreso(total)
        c = con.cursor()
        c.execute("select distinct municipio from estaciones where red || '--' || id in (select red || '--' || estacion from itinerarios where red=? and linea=?) order by municipio" , linea)
        municipios = c.fetchall()
        c.close()
        munis=[]
        for m in municipios:
            munis.append(m[0])
        if len(munis)>0:
            muni = ", ".join(munis)
            c = con.cursor()
            c.execute("UPDATE lineas set municipio=? where red=? and id=?", (muni , linea[0], linea[1]))
            con.commit()
            c.close()

    print ""

    c.close()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        rellenar_tablas()
        update_tablas()
    elif sys.argv[1] == "update":
        update_tablas()

    con.close()
