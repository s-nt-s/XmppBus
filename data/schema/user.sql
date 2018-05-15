DROP TABLE IF EXISTS marcadores;
DROP TABLE IF EXISTS tarjetas;
CREATE TABLE marcadores (user text, marcador text, cmd text, PRIMARY KEY (user, marcador));
CREATE TABLE tarjetas (user text, tarjeta text, PRIMARY KEY (user));
