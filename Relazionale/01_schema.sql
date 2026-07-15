-- ============================================================
--  DB RELAZIONALE - Negozio di elettronica
--  Creazione dello schema (SQLite)
-- ============================================================
--  Traccia: gestione di clienti, prodotti e ordini di un negozio di elettronica.
-- ============================================================

PRAGMA foreign_keys = ON;

-- Pulizia (utile se si rilancia lo script)
DROP TABLE IF EXISTS righe_ordine;
DROP TABLE IF EXISTS ordini;
DROP TABLE IF EXISTS prodotti;
DROP TABLE IF EXISTS categorie;
DROP TABLE IF EXISTS fornitori;
DROP TABLE IF EXISTS clienti;

-- ------------------------------------------------------------
-- CATEGORIE (es. smartphone, notebook, accessori)
-- ------------------------------------------------------------
CREATE TABLE categorie (
    codice_categoria INTEGER PRIMARY KEY,
    nome             TEXT NOT NULL UNIQUE
);

-- ------------------------------------------------------------
-- FORNITORI
-- ------------------------------------------------------------
CREATE TABLE fornitori (
    codice_fornitore INTEGER PRIMARY KEY,
    ragione_sociale  TEXT NOT NULL,
    telefono         TEXT,
    email            TEXT
);

-- ------------------------------------------------------------
-- CLIENTI
-- ------------------------------------------------------------
CREATE TABLE clienti (
    codice_cliente INTEGER PRIMARY KEY,
    nome           TEXT NOT NULL,
    cognome        TEXT NOT NULL,
    email          TEXT UNIQUE,
    telefono       TEXT,
    citta          TEXT
);

-- ------------------------------------------------------------
-- PRODOTTI
--   Ogni prodotto appartiene a una categoria ed e' fornito da un fornitore.
-- ------------------------------------------------------------
CREATE TABLE prodotti (
    codice_prodotto       INTEGER PRIMARY KEY,
    nome                  TEXT NOT NULL,
    descrizione           TEXT,
    prezzo_unitario       REAL NOT NULL CHECK (prezzo_unitario >= 0),
    quantita_disponibile  INTEGER NOT NULL DEFAULT 0 CHECK (quantita_disponibile >= 0),
    codice_categoria      INTEGER NOT NULL,
    codice_fornitore      INTEGER NOT NULL,
    FOREIGN KEY (codice_categoria) REFERENCES categorie(codice_categoria),
    FOREIGN KEY (codice_fornitore) REFERENCES fornitori(codice_fornitore)
);

-- ------------------------------------------------------------
-- ORDINI
--   Ogni ordine e' effettuato da un cliente in una certa data.
-- ------------------------------------------------------------
CREATE TABLE ordini (
    codice_ordine  INTEGER PRIMARY KEY,
    codice_cliente INTEGER NOT NULL,
    data_ordine    TEXT NOT NULL,            -- formato 'YYYY-MM-DD'
    FOREIGN KEY (codice_cliente) REFERENCES clienti(codice_cliente)
);

-- ------------------------------------------------------------
-- RIGHE_ORDINE
--   Ogni ordine contiene una o piu' righe, ciascuna riferita a un prodotto con quantita' e prezzo applicato al momento dell'acquisto.
-- ------------------------------------------------------------
CREATE TABLE righe_ordine (
    codice_ordine    INTEGER NOT NULL,
    codice_prodotto  INTEGER NOT NULL,
    quantita         INTEGER NOT NULL CHECK (quantita > 0),
    prezzo_applicato REAL NOT NULL CHECK (prezzo_applicato >= 0),
    PRIMARY KEY (codice_ordine, codice_prodotto),
    FOREIGN KEY (codice_ordine)   REFERENCES ordini(codice_ordine),
    FOREIGN KEY (codice_prodotto) REFERENCES prodotti(codice_prodotto)
);
