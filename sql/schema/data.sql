DROP TABLE IF EXISTS ids_itinerarios;
DROP TABLE IF EXISTS itinerarios;
DROP TABLE IF EXISTS lineas;
DROP TABLE IF EXISTS estaciones;
DROP TABLE IF EXISTS municipios;

CREATE TABLE municipios (
    cod_prov TEXT,
    cod_muni TEXT,
    municipio TEXT NOT NULL,
    PRIMARY KEY (cod_prov, cod_muni)
);
CREATE TABLE estaciones (
    red INTEGER,
    id INTEGER,
    cod TEXT NOT NULL,
    direccion TEXT,
    municipio TEXT,
    denominacion TEXT,
    cp INTEGER,
    PRIMARY KEY (red, id)
);
CREATE TABLE lineas (
    red INTEGER,
    id TEXT,
    cod TEXT NOT NULL,
    municipio TEXT,
    PRIMARY KEY (red, id)
);
CREATE TABLE itinerarios (
    red INTEGER,
    itinerario INTEGER,
    orden INTEGER,
    sentido INTEGER NOT NULL,
    linea TEXT NOT NULL,
    sublinea TEXT,
    estacion INTEGER NOT NULL,
    PRIMARY KEY (red, itinerario, orden),
    FOREIGN KEY (linea) REFERENCES lineas(id),
    FOREIGN KEY (estacion) REFERENCES estaciones(id)
);
CREATE TABLE ids_itinerarios (
    red INTEGER,
    id INTEGER,
    linea TEXT NOT NULL,
    sublinea TEXT,
    sentido INTEGER,
    PRIMARY KEY (red, id),
    FOREIGN KEY (id) REFERENCES itinerarios(itinerario)
);
