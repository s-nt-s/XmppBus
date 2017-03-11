#!/usr/bin/python

import time
import requests
import json
import os
import sys
import time
import re
import os

madrid = re.compile(
    r"\s*Madrid\s+\(\s*(.*?)\s*\)\s*$", re.MULTILINE | re.UNICODE)

url1 = "http://www.cuantotardamiautobus.es/madrid/tiempos.php?t="
cmp1 = "ids_parada"
url2 = "http://api.interurbanos.welbits.com/v1/stop/"

to_int = ["segundos", "distancia"]


def get_json(url):
    response = requests.get(url)
    if response.status_code != 200:
        return []
    js = response.json()
    if "lines" in js:
        return js["lines"]
    return js


def tiempos(paradas):
    t = time.time()
    param = str(t).replace(".", "")
    c = 0
    for i in range(0, len(paradas)):
        param = param + "&" + cmp1 + "[" + str(i) + "]=" + paradas[i]

    j = get_json(url1 + param)

    visto = []
    for x in range(len(j) - 1, -1, -1):
        i = j[x]
        for t in to_int:
            i[t] = int(i[t])
        if i["segundos"] == 999999 and i["linea"] in visto:
            del j[x]
            continue
        visto.append(i["linea"])

    for p in paradas:
        lines = get_json(url2 + p)
        for i in lines:
            if i["waitTime"] == "<<<":
                i["waitTime"] = "0 min"
            if i["lineNumber"] not in visto and " min" in i["waitTime"]:
                o = {}
                o["linea"] = i["lineNumber"]
                o["segundos"] = int(i["waitTime"].split()[0]) * 60
                o["destino"] = i["lineBound"]
                o["parada"] = p
                if madrid.match(o["destino"]):
                    o["destino"] = madrid.sub(r"\1", o["destino"])
                j.append(o)

    rst = sorted(j, key=lambda x: x['segundos'])
    return rst


def pt(info):
    r = ""
    lt = 0
    ll = 0
    for i in info:
        if i["segundos"] == 999999:
            m = "+20"
        else:
            m = str(i["segundos"] / 60)
        i["t"] = m
        lt = max(len(str(m)), lt)
        ll = max(len(i["linea"]), ll)

    for i in info:
        msg = "%" + str(lt) + "s min %" + str(ll) + "s -> " + i["destino"]
        msg = msg % (i["t"], i["linea"])
        r = r + msg + "\n"
    return r.rstrip()

if __name__ == "__main__":
    r = tiempos(sys.argv[1:])
    # print json.dumps(r, indent=4, sort_keys=True)
    print pt(r)
