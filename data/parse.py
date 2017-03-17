#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import glob
import csv
import os


if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

HEAD_LINEA = 'NUMEROLINEAUSUARIO'
HEAD_SENTIDO = 'SENTIDO'
HEAD_SUBLINEA = 'CODIGOSUBLINEA'
HEAD_ORDEN = 'NUMEROORDEN'
HEAD_PARADA = 'CODIGOESTACION'
HEAD_DIRECCION = 'DIRECCION'
HEAD_MUNICIPIO = 'MUNICIPIO'
HEAD_DENOMINACION = 'DENOMINACION'
HEAD_CODIGOEMPRESA = 'CODIGOEMPRESA'
HEAD_IDESTACION = 'IDESTACION'


sp = re.compile(r"\s+", re.MULTILINE | re.UNICODE)
sn = re.compile(r"( SN *)+$| N S\/N *$", re.UNICODE)
cn = re.compile(r" N (\d+[A-Z]?)$", re.UNICODE)
pr1 = re.compile(r"\( +")
pr2 = re.compile(r" +\)")
el = re.compile(r"^([^,]+), +(El|La) *$", re.UNICODE)
pre = re.compile(r"\b([A-Z]º)", re.UNICODE)


arti=" (de las|de la|del|de)? *"
subs=[
    re.compile("Calle"+arti, re.UNICODE | re.IGNORECASE),
    "c/ ",
    re.compile("Plaza"+arti, re.UNICODE | re.IGNORECASE),
    "Pl ",
    re.compile("(Avenida|Avda)"+arti, re.UNICODE | re.IGNORECASE),
    "Avda ",
    re.compile("Paseo"+arti, re.UNICODE | re.IGNORECASE),
    "Pº ",
    re.compile("Ronda"+arti, re.UNICODE | re.IGNORECASE),
    "Rda ",
]


indices = [ i[6] for i in glob.glob('csv/em*.csv') ]

def hash_estaciones(i):
    obj={}
    with open('csv/em'+i+'.csv', 'rb') as csvfile:
        sr = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        next(sr, None)
        for row in sr:
            if HEAD_CODIGOEMPRESA not in row or HEAD_IDESTACION not in row:
                continue
            a=row[HEAD_PARADA]
            b=row[HEAD_CODIGOEMPRESA]
            if b and len(b)>0:
                obj[a]=b
    return obj

def lineas(i):
    lst=[]
    with open('csv/pm'+i+'.csv', 'rb') as csvfile:
        sr = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        next(sr, None)
        for row in sr:
            if HEAD_LINEA not in row:
                continue
            l=row[HEAD_LINEA]
            if l not in lst:
                lst.append(l)
    return lst

def paradas(linea, i):
    lst=[]
    with open('csv/pm'+i+'.csv', 'rb') as csvfile:
        sr = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        next(sr, None)
        for row in sr:
            if HEAD_LINEA in row and row[HEAD_LINEA]==linea:
                lst.append(row)
    return lst

def sentidos(paradas):
    st=[]
    for row in paradas:
        if row[HEAD_SENTIDO] not in st:
            s=row[HEAD_SENTIDO]
            st.append(s)
            d="txt/" + s
            if not os.path.exists(d):
                os.makedirs(d)
    return st

def title(s):
    s=unicode(s).title()
    s=s.replace(" De La "," de la ")
    s=s.replace(" De Las "," de las ")
    s=s.replace(" Del "," del ")
    s=s.replace(" De "," de ")
    s=s.replace(" y "," y ")
    return s

def itinerario(cod, linea, sentido, obj):
    linea_filter = filter(lambda l: l[HEAD_SENTIDO] == sentido, linea)
    linea_filter = sorted(linea_filter,key=lambda l: int(l[HEAD_ORDEN]), reverse=False)
    paradas_vistas=[]
    for i in range(len(linea_filter)-1,-1,-1):
        l=linea_filter[i]
        p=l[HEAD_PARADA]
        if p in paradas_vistas:
            del linea_filter[i]
        else:
            paradas_vistas.append(p)
            muni=l[HEAD_MUNICIPIO]
            muni=title(muni)
            muni=el.sub(r"\2 \1",muni)
            muni=sp.sub(" ",muni).strip()
            l[HEAD_MUNICIPIO]=muni
            dire=sp.sub(" ",l[HEAD_DIRECCION]).strip()
            dire=sn.sub("",dire)
            dire=cn.sub(r" \1",dire)
            dire=pr1.sub(r"(", dire)
            dire=pr2.sub(r"(", dire)
            dire=title(dire)
            for i in range(0,len(subs),2):
                dire=subs[i].sub(subs[i+1],dire)
            l[HEAD_DIRECCION]=dire
            demo=l[HEAD_DENOMINACION]
            demo=demo.replace("-", " - ")
            demo=demo.replace(".", ". ")
            demo=pre.sub(r"\1 ",demo)
            demo=sp.sub(" ",demo).strip()
            demo=title(demo)
            l[HEAD_DENOMINACION]=demo


    pmn=False
    mn=linea_filter[0][HEAD_MUNICIPIO]
    lt=0
    for l in linea_filter:
        if l[HEAD_MUNICIPIO]!=mn:
            pmn=True
        lt=max(len(str(l[HEAD_PARADA])), lt)


    msg = "%" + str(lt) + "s %s"

    ruta="txt/" + sentido.upper() + "/" + cod.upper() + ".txt"
    with open(ruta, "wb") as f:
            
        for l in linea_filter:
            #print l[HEAD_SUBLINEA]+"  "+l[HEAD_ORDEN]+"\t"+l[HEAD_PARADA]+"\t"+demo+"\t"+dire+", "+muni
            p=l[HEAD_PARADA]
            if p in obj:
                p=obj[p]

            item = (msg % (p, l[HEAD_DIRECCION]))
            if pmn:
                item = item + ", "+l[HEAD_MUNICIPIO]
            
            f.write(item+"\n")

                    
if __name__ == "__main__":
    _linea = sys.argv[1] if len(sys.argv)>1 else None
    _sentido = [sys.argv[2]] if len(sys.argv)>2 else None

    for i in indices:
        lns = lineas(i)
        if _linea:
            if _linea not in lns:
                continue
            lns=[_linea]
        obj = hash_estaciones(i)

        for l in lns:
            prd=paradas(l, i)
            st = sentidos(prd) if _sentido is None else _sentido
            for s in st:
                itinerario(l, prd, s, obj)

