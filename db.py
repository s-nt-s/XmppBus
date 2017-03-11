import sqlite3

database = "bus.db"


def get(user, alias):
    con = sqlite3.connect(database)
    c = con.cursor()
    c.execute("select cmd from alias where user=? and alias=?", (user, alias))
    r = c.fetchone()
    c.close()
    con.commit()
    con.close()
    if r and len(r) > 0:
        return r[0]
    return None


def set(user, alias, cmd):
    con = sqlite3.connect(database)
    c = con.cursor()
    c.execute(
        "insert or replace into alias (user, alias, cmd) values (?, ?, ?)", (user, alias, cmd))
    c.close()
    con.commit()
    con.close()


def get_alias(user):
    con = sqlite3.connect(database)
    c = con.cursor()
    c.execute(
        "select alias, cmd from alias where user=? and alias!='.'", (user,))
    r = c.fetchall()
    c.close()
    con.commit()
    con.close()
    return r

if __name__ == "__main__":
    con = sqlite3.connect(database)
    c = con.cursor()
    c.execute("DROP TABLE IF EXISTS alias")
    c.execute(
        "CREATE TABLE alias (user text, alias text, cmd text, PRIMARY KEY (user, alias))")
    con.commit()
    con.close()
