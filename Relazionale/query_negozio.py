"""
============================================================
 DB RELAZIONALE - Negozio di elettronica
 Script Python che si connette al database SQLite ed esegue
 le query richieste dalla traccia.
============================================================

Prerequisiti:
  - Python 3
  - Il file 'negozio.db' deve essere presente nella stessa
    cartella. Se non c'e', lo si puo' rigenerare con:
        python query_negozio.py --crea
    (lo script ricostruira' il DB a partire dai file .sql).

Esecuzione:
    python query_negozio.py
"""

import os
import sqlite3
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "negozio.db")


def crea_database():
    """Ricrea il database eseguendo gli script 01_schema.sql e 02_insert.sql."""
    base = os.path.dirname(__file__)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for nome_file in ("01_schema.sql", "02_insert.sql"):
        with open(os.path.join(base, nome_file), "r", encoding="utf-8") as f:
            cur.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"Database creato in: {DB_PATH}\n")


def stampa_risultato(titolo, descrizione, righe):
    print("=" * 60)
    print(titolo)
    print(descrizione)
    print("-" * 60)
    for r in righe:
        print(r)
    print()


def main():
    # Se richiesto (o se il DB non esiste) lo si ricostruisce
    if "--crea" in sys.argv or not os.path.exists(DB_PATH):
        crea_database()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ----------------------------------------------------------
    # QUERY 1 - Prodotti acquistati da un determinato cliente
    # ----------------------------------------------------------
    codice_cliente = 1  # Marco Rossi
    cur.execute(
        """
        SELECT DISTINCT p.codice_prodotto, p.nome, cat.nome AS categoria
        FROM clienti c
        JOIN ordini o        ON c.codice_cliente = o.codice_cliente
        JOIN righe_ordine r  ON o.codice_ordine  = r.codice_ordine
        JOIN prodotti p      ON r.codice_prodotto = p.codice_prodotto
        JOIN categorie cat   ON p.codice_categoria = cat.codice_categoria
        WHERE c.codice_cliente = ?
        ORDER BY p.nome
        """,
        (codice_cliente,),
    )
    stampa_risultato(
        "QUERY 1 - Prodotti acquistati dal cliente",
        f"Cliente con codice = {codice_cliente}",
        cur.fetchall(),
    )

    # ----------------------------------------------------------
    # QUERY 2 - Totale speso da ciascun cliente
    # ----------------------------------------------------------
    cur.execute(
        """
        SELECT c.codice_cliente, c.nome, c.cognome,
               ROUND(SUM(r.quantita * r.prezzo_applicato), 2) AS totale_speso
        FROM clienti c
        JOIN ordini o       ON c.codice_cliente = o.codice_cliente
        JOIN righe_ordine r ON o.codice_ordine  = r.codice_ordine
        GROUP BY c.codice_cliente, c.nome, c.cognome
        ORDER BY totale_speso DESC
        """
    )
    stampa_risultato(
        "QUERY 2 - Totale speso da ciascun cliente",
        "(codice, nome, cognome, totale speso in euro)",
        cur.fetchall(),
    )

    # ----------------------------------------------------------
    # QUERY 3 - Spesa media mensile per cliente (anno 2025)
    # ----------------------------------------------------------
    anno = "2025"
    cur.execute(
        """
        SELECT m.codice_cliente, cl.nome, cl.cognome,
               ROUND(AVG(m.totale_mese), 2) AS spesa_media_mensile
        FROM (
            SELECT o.codice_cliente,
                   strftime('%Y-%m', o.data_ordine) AS mese,
                   SUM(r.quantita * r.prezzo_applicato) AS totale_mese
            FROM ordini o
            JOIN righe_ordine r ON o.codice_ordine = r.codice_ordine
            WHERE strftime('%Y', o.data_ordine) = ?
            GROUP BY o.codice_cliente, mese
        ) AS m
        JOIN clienti cl ON cl.codice_cliente = m.codice_cliente
        GROUP BY m.codice_cliente, cl.nome, cl.cognome
        ORDER BY spesa_media_mensile DESC
        """,
        (anno,),
    )
    stampa_risultato(
        f"QUERY 3 - Spesa media mensile per cliente (anno {anno})",
        "(codice, nome, cognome, spesa media mensile in euro)",
        cur.fetchall(),
    )

    # ----------------------------------------------------------
    # QUERY 4 - Coppie di prodotti acquistati piu' spesso insieme
    # ----------------------------------------------------------
    cur.execute(
        """
        SELECT p1.nome AS prodotto_A,
               p2.nome AS prodotto_B,
               COUNT(*) AS volte_insieme
        FROM righe_ordine r1
        JOIN righe_ordine r2
          ON r1.codice_ordine = r2.codice_ordine
         AND r1.codice_prodotto < r2.codice_prodotto
        JOIN prodotti p1 ON p1.codice_prodotto = r1.codice_prodotto
        JOIN prodotti p2 ON p2.codice_prodotto = r2.codice_prodotto
        GROUP BY p1.nome, p2.nome
        ORDER BY volte_insieme DESC, prodotto_A
        """
    )
    stampa_risultato(
        "QUERY 4 - Coppie di prodotti acquistati insieme",
        "(prodotto A, prodotto B, numero di ordini in cui compaiono insieme)",
        cur.fetchall(),
    )

    # ----------------------------------------------------------
    # QUERY 5 - Ultimo ordine, giorni di inattivita' e valore cliente
    # ----------------------------------------------------------
    cur.execute(
        """
        SELECT c.nome || ' ' || c.cognome AS cliente,
               MAX(o.data_ordine) AS ultimo_ordine,
               CAST(julianday((SELECT MAX(data_ordine) FROM ordini))
                    - julianday(MAX(o.data_ordine)) AS INT) AS giorni_inattivo,
               ROUND(SUM(r.quantita * r.prezzo_applicato), 2) AS valore_cliente
        FROM clienti c
        JOIN ordini o       ON c.codice_cliente = o.codice_cliente
        JOIN righe_ordine r ON o.codice_ordine  = r.codice_ordine
        GROUP BY c.codice_cliente
        ORDER BY giorni_inattivo DESC, valore_cliente DESC
        """
    )
    stampa_risultato(
        "QUERY 5 - Inattivita' e valore per cliente",
        "(cliente, ultimo ordine, giorni di inattivita', valore totale in euro)",
        cur.fetchall(),
    )

    conn.close()


if __name__ == "__main__":
    main()
