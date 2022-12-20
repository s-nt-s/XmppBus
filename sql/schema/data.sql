DROP TABLE IF EXISTS ids_itinerario;
DROP TABLE IF EXISTS itinerario;
DROP TABLE IF EXISTS linea;
DROP TABLE IF EXISTS estacion;
DROP TABLE IF EXISTS municipio;

CREATE TABLE red (
    id INTEGER,
    txt TEXT,
    PRIMARY KEY (id)
);
INSERT into red (id, txt) VALUES
(4, 'Metro'),
(5, 'Cercanías'),
(6, 'Autobus urbano Madrid'),
(8, 'Autobus interurbano'),
(9, 'Autobus urbano excepto Madrid'),
(10, 'Metro ligero / Tranvía');


CREATE TABLE municipio (
    id TEXT,
    txt TEXT NOT NULL,
    label TEXT NOT NULL,
    PRIMARY KEY (id)
);
CREATE TABLE estacion (
    red INTEGER,
    id INTEGER,
    cod TEXT NOT NULL,
    direccion TEXT,
    municipio TEXT,
    denominacion TEXT,
    cp INTEGER,
    PRIMARY KEY (red, id),
    FOREIGN KEY (red) REFERENCES red(id),
    FOREIGN KEY (municipio) REFERENCES municipio(id)
);
CREATE TABLE linea (
    red INTEGER,
    id TEXT NOT NULL,
    cod TEXT NOT NULL,
    municipio TEXT NOT NULL,
    municipios TEXT NOT NULL,
    denominacion TEXT NOT NULL,
    PRIMARY KEY (red, id),
    FOREIGN KEY (red) REFERENCES red(id),
    FOREIGN KEY (municipio) REFERENCES municipio(id)
);
CREATE TABLE itinerario (
    red INTEGER,
    id INTEGER,
    orden INTEGER,
    sentido INTEGER NOT NULL,
    linea TEXT NOT NULL,
    sublinea TEXT,
    estacion INTEGER NOT NULL,
    PRIMARY KEY (red, id, orden),
    --FOREIGN KEY (red) REFERENCES red(id),
    FOREIGN KEY (red, linea) REFERENCES linea(red, id),
    FOREIGN KEY (red, estacion) REFERENCES estacion(red, id)
);
CREATE TABLE ids_itinerario (
    red INTEGER,
    id INTEGER,
    linea TEXT NOT NULL,
    sublinea TEXT,
    sentido INTEGER,
    PRIMARY KEY (red, id),
    --FOREIGN KEY (red) REFERENCES red(id),
    FOREIGN KEY (red, id) REFERENCES itinerario(red, id)
);
