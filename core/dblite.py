import errno
import logging
import os
import re
import sqlite3
from os.path import isfile
from textwrap import dedent

re_select = re.compile(r"^\s*select\b")
re_sp = re.compile(r"\s+")
re_largefloat = re.compile("(\d+\.\d+e-\d+)")
re_bl = re.compile(r"\n\s*\n", re.IGNORECASE)


def save(file, content):
    if file and content:
        content = dedent(content).strip()
        with open(file, "w") as f:
            f.write(content)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def one_factory(cursor, row):
    return row[0]


def ResultIter(cursor, size=1000):
    while True:
        results = cursor.fetchmany(size)
        if not results:
            break
        for result in results:
            yield result


class CaseInsensitiveDict(dict):
    @classmethod
    def _k(cls, key):
        return key.lower() if isinstance(key, str) else key

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._convert_keys()

    def __getitem__(self, key):
        return super().__getitem__(self.__class__._k(key))

    def __setitem__(self, key, value):
        super().__setitem__(self.__class__._k(key), value)

    def __delitem__(self, key):
        return super().__delitem__(self.__class__._k(key))

    def __contains__(self, key):
        return super().__contains__(self.__class__._k(key))

    def has_key(self, key):
        return super().has_key(self.__class__._k(key))

    def pop(self, key, *args, **kwargs):
        return super().pop(self.__class__._k(key), *args, **kwargs)

    def get(self, key, *args, **kwargs):
        return super().get(self.__class__._k(key), *args, **kwargs)

    def setdefault(self, key, *args, **kwargs):
        return super().setdefault(self.__class__._k(key), *args, **kwargs)

    def update(self, E=None, **F):
        if E is not None:
            E = self.__class__(E)
        F = self.__class__(**F)
        super().update(E=E, **F)

    def _convert_keys(self):
        for k in list(self.keys()):
            v = super().pop(k)
            self.__setitem__(k, v)


def get_db(file, *extensions, readonly=False):
    logging.info("sqlite: " + file)
    if readonly:
        file = "file:" + file + "?mode=ro"
        con = sqlite3.connect(file, uri=True)
    else:
        con = sqlite3.connect(file)
    if extensions:
        con.enable_load_extension(True)
        for e in extensions:
            con.load_extension(e)
    return con


class DBLite:
    def __init__(self, file, extensions=None, reload=False, readonly=False):
        self.readonly = readonly
        self.file = file
        if reload and isfile(self.file):
            os.remove(self.file)
        if self.readonly and not isfile(self.file):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), file)
        self.extensions = extensions or []
        self._tables = None
        self.inTransaction = False
        self.con = get_db(self.file, *self.extensions, readonly=self.readonly)

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def openTransaction(self):
        if self.inTransaction:
            self.con.execute("END TRANSACTION")
        self.con.execute("BEGIN TRANSACTION")
        self.inTransaction = True

    def closeTransaction(self):
        if self.inTransaction:
            self.con.execute("END TRANSACTION")
            self.inTransaction = False

    @property
    def indices(self):
        for i, in self.select("SELECT name FROM sqlite_master WHERE type='index' order by name"):
            yield i

    @property
    def tables(self):
        if self._tables is None:
            self._tables = CaseInsensitiveDict()
            for t, in list(self.select("SELECT name FROM sqlite_master WHERE type='table'")):
                self._tables[t] = self.get_cols(
                    "select * from `" + t + "` limit 0")
        return self._tables

    def get_cols(self, sql):
        _sql = sql.lower().split()
        if len(_sql) < 2 and _sql[-1] != "limit":
            sql = sql + " limit 1"
        cursor = self.con.cursor()
        cursor.execute(sql)
        cols = tuple(col[0] for col in cursor.description)
        cursor.close()
        return cols

    def insert(self, table, insert_or=None, **kwargs):
        ok_keys = [k.upper() for k in self.tables[table]]
        keys = []
        vals = []
        for k, v in kwargs.items():
            if v is None or (isinstance(v, str) and len(v) == 0):
                continue
            if k.upper() not in ok_keys:
                continue
            keys.append('"' + k + '"')
            vals.append(v)
        prm = ['?'] * len(vals)
        sql = "insert"
        if insert_or:
            sql = "insert or " + insert_or
        sql = sql + " into %s (%s) values (%s)" % (
            table, ', '.join(keys), ', '.join(prm))
        self.con.execute(sql, vals)

    def _build_select(self, sql):
        sql = sql.strip()
        if not sql.lower().startswith("select"):
            field = "*"
            if "." in sql:
                sql, field = sql.rsplit(".", 1)
            sql = "select " + field + " from " + sql
        return sql

    def commit(self):
        self.con.commit()

    def close(self, vacuum=False):
        if self.readonly:
            self.con.close()
            return
        self.closeTransaction()
        self.con.commit()
        if vacuum:
            c = self.con.execute("pragma integrity_check")
            c = c.fetchone()
            print("integrity_check =", *c)
            self.con.execute("VACUUM")
        self.con.commit()
        self.con.close()

    def select(self, sql, *args, row_factory=None, **kwargs):
        sql = self._build_select(sql)
        self.con.row_factory = row_factory
        cursor = self.con.cursor()
        if len(args):
            cursor.execute(sql, args)
        else:
            cursor.execute(sql)
        for r in ResultIter(cursor):
            yield r
        cursor.close()
        self.con.row_factory = None

    def to_list(self, *args, **kvargs):
        r = list(self.select(*args, **kvargs))
        if len(r) > 0 and isinstance(r[0], tuple) and len(r[0]) == 1:
            r = [i[0] for i in r]
        return r

    def one(self, sql, *args):
        sql = self._build_select(sql)
        cursor = self.con.cursor()
        if len(args):
            cursor.execute(sql, args)
        else:
            cursor.execute(sql)
        r = cursor.fetchone()
        cursor.close()
        if not r:
            return None
        if len(r) == 1:
            return r[0]
        return r

    def get_sql_table(self, table):
        sql = "SELECT sql FROM sqlite_master WHERE type='table' AND name=?"
        cursor = self.con.cursor()
        cursor.execute(sql, (table,))
        sql = cursor.fetchone()[0]
        cursor.close()
        return sql

    def execute(self, sql, *args, to_file=None):
        if isfile(sql):
            with open(sql, "r") as f:
                sql = f.read()
        save(to_file, sql)
        if len(args):
            self.con.execute(sql, args)
        else:
            self.con.executescript(sql)
        self.con.commit()
        self._tables = None
