CREATE TABLE mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tema TEXT NOT NULL,
    texto TEXT NOT NULL,
    creado INTEGER NOT NULL
);

CREATE TABLE buzon (
    id TEXT PRIMARY KEY,
    blob BLOB NOT NULL,
    expira INTEGER NOT NULL
);

CREATE TABLE directorio (
    nodo TEXT PRIMARY KEY,
    entrada TEXT NOT NULL,
    firma TEXT NOT NULL,
    expira INTEGER NOT NULL
);

CREATE TABLE nonces (
    nonce TEXT PRIMARY KEY,
    expira INTEGER NOT NULL
);
