import re

DAYNAME = ['Lunes', 'Martes', 'Miércoles',
           'Jueves', 'Viernes', 'Sábado', 'Domingo']

re_url = re.compile(
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
re_mail = re.compile(
    r"^([a-záéíóú0-9_\-\.]+)@([a-záéíóú0-9_\-\.]+)\.([a-záéíóú]{2,5})$", re.IGNORECASE)
re_sp = re.compile(r"\s+")


def tmap(f, a):
    return tuple(map(f, a))


def parse_mes(m):
    if m is None:
        return None
    m = m.strip().lower()[:3]
    if m == "ene":
        return 1
    if m == "feb":
        return 2
    if m == "mar":
        return 3
    if m == "abr":
        return 4
    if m == "may":
        return 5
    if m == "jun":
        return 6
    if m == "jul":
        return 7
    if m == "ago":
        return 8
    if m == "sep":
        return 9
    if m == "oct":
        return 10
    if m == "nov":
        return 11
    if m == "dic":
        return 12
    return None


def parse_dia(d):
    d = d.weekday()
    return ["L", "M", "X", "J", "V", "S", "D"][d]


def to_num(s, safe=False):
    if s is None:
        return None
    if safe is True:
        try:
            return to_num(s)
        except ValueError:
            return s
    if isinstance(s, str):
        s = s.replace("€", "")
        s = s.replace(".", "")
        s = s.replace(",", ".")
        s = float(s)
    if int(s) == s:
        s = int(s)
    return s


def to_strint(f):
    if f is None:
        return None
    f = round(f)
    f = '{:,}'.format(f).replace(",", ".")
    return f


def notnull(*args, sep=None):
    arr = []
    for a in args:
        if isinstance(a, str):
            a = a.strip()
        if a not in (None, ""):
            arr.append(a)
    if sep:
        return sep.join(arr)
    return tuple(arr)

def yjoin(arr, singular='', plural=''):
    if len(arr) == 0:
        return ''
    if len(arr) == 1:
        return (singular + ' ' + arr[0]).strip()
    if len(arr) == 2:
        return (plural + ' ' + (" y ".join(arr))).strip()
    return (plural + ' ' + (", ".join(arr[:-1]) + " y " + arr[-1])).strip()