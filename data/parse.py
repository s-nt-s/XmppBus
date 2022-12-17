import csv as csvreader
import glob
from os.path import dirname, realpath
import re
import sys
from munch import Munch
from core.dbbus import DBLite

ROOT = dirname(realpath(__file__)) + '/'

HEAD_DIRECCION_ALT = ["TIPOVIA", "PARTICULA",
                      "NOMBREVIA", "TIPONUMERO", "NUMEROPORTAL"]
HEAD = {
    'CODIGOGESTIONLINEA': 'idLinea',
    'NUMEROLINEAUSUARIO': 'cdLinea',
    'CODIGOESTACION': 'idEstacion',
    'CODIGOEMPRESA': 'cdEstacion',
    'SENTIDO': 'sentido',
    'CODIGOSUBLINEA': 'sublinea',
    'NUMEROORDEN': 'orden',
    'DIRECCION': 'direccion',
    'MUNICIPIO': 'municipio',
    'CODIGOMUNICIPIO': 'cdMunicipio',
    'CODIGOPROVINCIA': 'cdProvincia',
    'DENOMINACION': 'denominacion',
    'CODIGOPOSTAL': 'cp',
    'CODIGOITINERARIO': 'idItinerario',
}

REDES = tuple(("6", "8", "9"))

re_sp = re.compile(r"\s+", re.MULTILINE | re.UNICODE)
re_sn = re.compile(r"( SN *)+$| N S\/N *$", re.UNICODE)
re_cn = re.compile(r" Nº? (\d+[A-Z]?)$", re.UNICODE)
re_pr1 = re.compile(r"\( +")
re_pr2 = re.compile(r" +\)")
re_el = re.compile(r"^([^,]+), +(El|Las|La) *$", re.UNICODE)
re_pre = re.compile(r"\b([A-Z]º)", re.UNICODE)
re_cleanlinea = re.compile(r"[¡]", re.UNICODE)

arti = " (de las|de la|del|de)? *"
re_subs = [
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


def title(s):
    s = s.title()
    s = s.replace(" De La ", " de la ")
    s = s.replace(" De Las ", " de las ")
    s = s.replace(" Del ", " del ")
    s = s.replace(" De ", " de ")
    s = s.replace(" Y ", " y ")
    return s


def wrflush(line, *args, **kvargs):
    if args or kvargs:
        line = line.format(*args, **kvargs)
    sys.stdout.write(line)
    sys.stdout.flush()


def iterprogress(arr):
    arr = list(arr)
    tot = len(arr)
    for current, elm in enumerate(arr):
        prct = (current * 100) / tot
        if (current % 10) == 0:
            wrflush("\r{:3.0f}% de {:5.0f}", prct, tot)
        yield elm
    wrflush("\r{:3.0f}% de {:5.0f}", 100, tot)
    print("")


def read_csv(file):
    red = re.match(r".*_(\d+).csv", file)
    if red:
        red = int(red.group(1))
    with open(file, 'r') as csvfile:
        sr = csvreader.DictReader(csvfile, delimiter=',', quotechar='"')
        keys = set(next(sr).keys())
        rows = list(sr)
    altDr = len(set(HEAD_DIRECCION_ALT) - keys) == 0
    for row in iterprogress(rows):
        rtn = {}
        for k, v in list(row.items()):
            k = HEAD.get(k, k)
            if isinstance(v, str):
                v = re_sp.sub(" ", v).strip()
                if k == 'cdLinea':
                    v = re_cleanlinea.sub("", v)
                if k in ('idLinea', 'cdLinea'):
                    v = v.upper()
                if k in ('orden', 'idItinerario', 'sentido', 'idEstacion'):
                    v = int(v)
            rtn[k] = v
        if altDr and not rtn.get('direccion'):
            rtn['direccion'] = ""
            for h in HEAD_DIRECCION_ALT:
                rtn['direccion'] = rtn['direccion'] + " " + row[h]
            rtn['direccion'] = re_sp.sub(" ", rtn['direccion']).strip()
        if red is not None:
            rtn['red'] = red
        yield Munch.fromDict(rtn)


class DBData(DBLite):
    def __init__(self, reload=False, **kvargs):
        super().__init__(ROOT + "data.db", reload=reload, **kvargs)
        if len(self.tables) == 0:
            self.execute(ROOT + "../sql/schema/data.sql")

    def get_municipio(self, row):
        if 'municipio' in row:
            return row.municipio
        cod_prov = row.cdProvincia
        cod_muni = row.cdMunicipio
        return self.one("select municipio from municipios where cod_prov=? and cod_muni=?", cod_prov, cod_muni)


def dire_muni_demo(dire, muni, demo):
    muni = title(muni)
    muni = re_el.sub(r"\2 \1", muni)
    muni = re_sp.sub(" ", muni).strip()

    dire = re_sp.sub(" ", dire).strip()
    dire = re_sn.sub("", dire)
    dire = re_cn.sub(r" \1", dire)
    dire = re_pr1.sub(r"(", dire)
    dire = re_pr2.sub(r"(", dire)
    dire = title(dire)
    for i in range(0, len(re_subs), 2):
        dire = re_subs[i].sub(re_subs[i + 1], dire)

    demo = demo.replace("-", " - ")
    demo = demo.replace(".", ". ")
    demo = re_pre.sub(r"\1 ", demo)
    demo = re_sp.sub(" ", demo).strip()
    demo = re_sn.sub("", demo)
    demo = re_cn.sub(r" \1", demo)
    demo = title(demo)

    return dire, muni, demo


def rellenar_tablas():
    with DBData(reload=True) as db:
        for _csv in sorted(glob.glob(ROOT + "csv/*.csv"), key=lambda x:tuple(reversed(x.rsplit("_", 1)))):
            print("# MUNICIPIOS " + _csv.rsplit("/", 1)[-1])
            for row in read_csv(_csv):
                if len(set(row.get(k) for k in ('cdMunicipio', 'cdProvincia', 'municipio')).intersection((None, ""))):
                    continue
                db.insert("municipios", cod_prov=row.cdProvincia, cod_muni=row.cdMunicipio, municipio=row.municipio,
                          insert_or="ignore")

        for i in REDES:
            i = str(i)
            print("\n# RED " + i)
            print("## LINEAS")
            visto = set()
            for row in read_csv(ROOT + 'csv/lineas_' + i + '.csv'):
                if row.idLinea in visto:
                    continue
                visto.add(row.idLinea)
                db.insert("lineas", red=row.red, id=row.idLinea, cod=row.cdLinea)
            print("## ESTACIONES")
            for row in read_csv(ROOT + 'csv/estaciones_' + i + '.csv'):
                id = row.idEstacion
                cd = row.cdEstacion
                dire, muni, demo = dire_muni_demo(row.direccion, db.get_municipio(row), row.denominacion)
                if len(cd) == 0:
                    cd = id
                db.insert("estaciones", red=row.red, id=id, cod=cd, direccion=dire, municipio=muni, denominacion=demo,
                          cp=row.cp)

            print("## ITINERARIOS")
            for row in read_csv(ROOT + 'csv/itinerario_' + i + '.csv'):
                db.insert("itinerarios",
                          red=row.red,
                          itinerario=row.idItinerario,
                          sentido=row.sentido,
                          linea=row.idLinea,
                          sublinea=row.sublinea,
                          estacion=row.idEstacion,
                          orden=row.orden
                          )

        print("# IDS_ITINERARIOS")

        db.execute('''
            INSERT INTO ids_itinerarios (red, id, linea, sublinea, sentido)
            SELECT distinct
                red, itinerario, linea, sublinea, sentido
            FROM itinerarios
        ''')


def update_tablas():
    print("# UPDATE LINEAS")
    with DBData(reload=False) as db:
        lineas = db.to_list("select red, id from lineas")
        for red, id in iterprogress(lineas):
            munis = db.to_list(
                "select distinct municipio from estaciones where red || '--' || id in (select red || '--' || estacion from itinerarios where red=? and linea=?) order by municipio",
                red, id)
            if len(munis) > 0:
                muni = ", ".join(munis)
                db.execute("UPDATE lineas set municipio=? where red=? and id=?", muni, red, id)


if __name__ == "__main__":
    flag = sys.argv[1] if len(sys.argv) > 1 else None
    if flag is None:
        rellenar_tablas()
        update_tablas()
        print("")
    elif flag == "update":
        update_tablas()
        print("")
    else:
        pass
    DBData(reload=False).close(vacuum=True)
    with DBData(reload=False, readonly=True) as db:
        for t in db.tables:
            count = db.one("select count(*) from " + t)
            print(t, count)
