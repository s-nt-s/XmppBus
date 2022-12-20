from subprocess import DEVNULL, STDOUT, check_call
from os.path import basename, realpath, isdir, isfile, dirname, relpath
from os import makedirs, getcwd, chdir
import tempfile
from PIL import Image
from urllib.request import urlretrieve
from textwrap import dedent
import argparse
import sys


class SchemasPy:
    def __init__(self, home=None):
        self.driver = "https://github.com/xerial/sqlite-jdbc/releases/download/3.32.3.2/sqlite-jdbc-3.32.3.2.jar"
        self.jar = "https://github.com/schemaspy/schemaspy/releases/download/v6.1.0/schemaspy-6.1.0.jar"
        self._driver = basename(self.driver)
        self._jar = basename(self.jar)
        self.home = home
        if self.home is None and isdir("schemaspy"):
            self.home = "schemaspy"
        if self.home is None:
            self.home = tempfile.mkdtemp()
        self.root = realpath(self.home) + "/"

    def dwn(self, url):
        name = basename(url)
        if isfile(self.root + name):
            return False
        print("$ wget", url)
        urlretrieve(url, self.root + name)
        return True

    def write(self, file, txt, overwrite=False):
        if not overwrite and isfile(file):
            return False
        with open(file, "w") as f:
            f.write(dedent(txt).strip())
        return True

    def report(self, file, *flags, out=None, **kargv):
        # https://github.com/schemaspy/schemaspy/issues/524#issuecomment-496010502
        if not isdir(self.home):
            makedirs(self.home, exist_ok=True)
        if out is None:
            out = tempfile.mkdtemp()

        reload_1 = self.dwn(self.jar)
        db = None
        cmd = ["java", "-jar", self._jar, "-o", out]
        out = realpath(out)
        if file.endswith(".properties"):
            cmd.extend([
                "-configFile",
                relpath(file, self.root),
            ])
        else:
            reload_2 = self.dwn(self.driver)
            reload = reload_1 or reload_2

            self.write(self.root + "sqlite.properties", '''
                driver=org.sqlite.JDBC
                description=SQLite
                driverPath={driver}
                connectionSpec=jdbc:sqlite:<db>
            '''.format(driver=self._driver), overwrite=reload)

            self.write(self.root + "schemaspy.properties", '''
                schemaspy.t=sqlite
                schemaspy.sso=true
            ''', overwrite=reload)

            self.write(self.root + "rename.sh", '''
                #!/bin/bash
                grep "$1" -l -r $2 | xargs -d '\\n' sed -i -e "s|${1}||g"
            ''', overwrite=True)

            name = basename(file)
            name = name.rsplit(".", 1)[0]
            db = realpath(file)
            cmd.extend([
                "-dp",
                self.root,
                "-db",
                db,
                "-cat",
                name,
                "-s",
                name,
                "-u",
                name
            ])
        for flag in flags:
            cmd.append(flag)
        for k, v in kargv.items():
            cmd.append("-"+k)
            cmd.append(str(v))

        current_dir = getcwd()
        chdir(self.root)
        print("$ cd", self.root)
        self.run(*cmd)
        if not file.endswith(".properties"):
            self.run("bash", "rename.sh", dirname(db) + "/", out)
        chdir(current_dir)

        print(out + "/index.html")
        return out

    def run(self, *args):
        def pr_arg(a):
            if isinstance(a, str) and ' ' in a:
                return "'"+a+"'"
            return a
        print("$", *map(pr_arg, args))
        check_call(args, stdout=DEVNULL, stderr=STDOUT)

    def save_diagram(self, db, img, *args, size="compact", **kargv):
        out = self.report(db, *args, **kargv)
        fl = out + "/diagrams/summary/relationships.real.{}.png".format(size)
        if not isfile(fl):
            print("No existen relaciones entre las tablas")
            return
        print("$ cp", fl, img)
        im = Image.open(fl)
        box = im.getbbox()
        box = list(box)
        box[3] = box[3] - 45
        gr = im.crop(tuple(box))
        gr.save(img)
        gr.close()
        im.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Obtener diagrama de una base de una base de datos")
    parser.add_argument('--out', help="Diagrama de salida", required=True)
    parser.add_argument('--host', help="Host")
    parser.add_argument('--port', type=int, help="Port")
    parser.add_argument('--user', help="Usuario")
    parser.add_argument('--password', help="Contraseña")
    parser.add_argument('--size', default="compact", help="Tamaño de la imagen")
    parser.add_argument('db', help='Base de datos sqlite o .properties')
    pargs = parser.parse_args()

    if not isfile(pargs.db):
        sys.exit(pargs.db + " no existe")

    extra = {k: v for k, v in {
        "u": pargs.user,
        "p": pargs.password,
        "host": pargs.host,
        "port": pargs.port
    }.items() if v is not None}

    s = SchemasPy()
    s.save_diagram(
        pargs.db,
        pargs.out,
        "-norows",
        "-noviews",
        size=pargs.size,
        **extra
    )
