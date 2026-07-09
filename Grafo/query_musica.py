"""
============================================================
 DB A GRAFO (Neo4j) - Piattaforma musicale
 Script Python che si connette a Neo4j ed esegue le query
 richieste dalla traccia.
============================================================

Prerequisiti:
  - Neo4j in esecuzione (vedi ISTRUZIONI_NEO4J.txt)
  - pip install neo4j
  - Aver caricato i dati con lo script 01_create.cypher
    (oppure lanciare:  python query_musica.py --crea )

IMPORTANTE: modificare URI / utente / password in base alla
propria installazione di Neo4j Desktop.

Esecuzione:
    python query_musica.py
"""

import os
import sys
from neo4j import GraphDatabase

# ---- Parametri di connessione (DA ADATTARE) ----------------
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "12345678")   # <-- inserire la password impostata in Neo4j Desktop


def carica_dati(session):
    """Esegue lo script Cypher di creazione del grafo."""
    base = os.path.dirname(__file__)
    with open(os.path.join(base, "01_create.cypher"), "r", encoding="utf-8") as f:
        script = f.read()
    # Lo script contiene piu' statement separati da ';'
    for statement in [s.strip() for s in script.split(";") if s.strip()]:
        # si saltano le righe di solo commento
        righe = [r for r in statement.splitlines() if not r.strip().startswith("//")]
        if "\n".join(righe).strip():
            session.run(statement)
    print("Grafo creato/popolato.\n")


def stampa(titolo, records):
    print("=" * 60)
    print(titolo)
    print("-" * 60)
    for rec in records:
        print(dict(rec))
    print()


def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    session = driver.session(database="neo4j")

    if "--crea" in sys.argv:
        carica_dati(session)

    utente = "Marco"

    # ----------------------------------------------------------
    # QUERY 1 - Brani consigliati in base ad artisti seguiti e
    #           generi piu' ascoltati
    # ----------------------------------------------------------
    # NOVITA' (LISTENED.conteggio): i generi preferiti si pesano con la
    # somma delle riproduzioni (sum(r.conteggio)) invece di count(*).
    q1 = """
    MATCH (u:User {username:$utente})
    MATCH (u)-[r:LISTENED]->(:Track)-[:OF_GENRE]->(g:Genre)
    WITH u, g, sum(r.conteggio) AS riproduzioni
    ORDER BY riproduzioni DESC
    WITH u, collect(g.name)[0..2] AS generiPreferiti
    MATCH (cand:Track)
    WHERE NOT (u)-[:LISTENED]->(cand)
    OPTIONAL MATCH (art:Artist)-[:PUBLISHED]->(:Album)-[:CONTAINS]->(cand)
    OPTIONAL MATCH (cand)-[:OF_GENRE]->(gg:Genre)
    WITH u, cand, art, generiPreferiti, collect(DISTINCT gg.name) AS generiBrano
    WITH cand, art, generiBrano,
         (CASE WHEN (u)-[:FOLLOWS]->(art) THEN 2 ELSE 0 END
          + size([x IN generiBrano WHERE x IN generiPreferiti])) AS score
    WHERE score > 0
    RETURN cand.title AS brano_consigliato, art.name AS artista,
           generiBrano AS generi, score AS punteggio
    ORDER BY punteggio DESC, brano_consigliato
    """
    stampa(
        f"QUERY 1 - Brani consigliati per l'utente '{utente}'",
        session.run(q1, utente=utente),
    )

    # ----------------------------------------------------------
    # QUERY 2 - Artisti collegati da ascoltatori comuni
    # ----------------------------------------------------------
    q2 = """
    MATCH (a1:Artist)-[:PUBLISHED]->(:Album)-[:CONTAINS]->(:Track)<-[:LISTENED]-(u:User),
          (u)-[:LISTENED]->(:Track)<-[:CONTAINS]-(:Album)<-[:PUBLISHED]-(a2:Artist)
    WHERE a1.name < a2.name
    RETURN a1.name AS artista_1, a2.name AS artista_2,
           count(DISTINCT u) AS ascoltatori_comuni
    ORDER BY ascoltatori_comuni DESC, artista_1, artista_2
    """
    stampa("QUERY 2 - Artisti collegati da ascoltatori comuni", session.run(q2))

    # ----------------------------------------------------------
    # QUERY 3 - Artisti a 2 hop: Utente -> Artista <- Utente -> Artista
    # ----------------------------------------------------------
    q3 = """
    MATCH (u:User {username:$utente})-[:FOLLOWS]->(:Artist)
          <-[:FOLLOWS]-(altro:User)-[:FOLLOWS]->(a2:Artist)
    WHERE NOT (u)-[:FOLLOWS]->(a2)
    RETURN a2.name AS artista_consigliato,
           count(DISTINCT altro) AS tramite_n_utenti
    ORDER BY tramite_n_utenti DESC, artista_consigliato
    """
    stampa(
        f"QUERY 3 - Artisti a 2 hop dall'utente '{utente}'",
        session.run(q3, utente=utente),
    )

    # ----------------------------------------------------------
    # QUERY 4 - Brani consigliati tramite filtering collaborativo
    #           (utenti con ascolti in comune)
    # ----------------------------------------------------------
    # NOVITA' (LISTENED.conteggio): il voto pesa per affinita' del vicino E
    # per quante volte il vicino ha riprodotto il brano (affinita * r2.conteggio).
    q4 = """
    MATCH (me:User {username:$utente})-[:LISTENED]->(t:Track)<-[:LISTENED]-(altro:User)
    WHERE altro <> me
    WITH me, altro, count(DISTINCT t) AS affinita
    MATCH (altro)-[r2:LISTENED]->(reco:Track)
    WHERE NOT (me)-[:LISTENED]->(reco)
    RETURN reco.title AS brano_consigliato,
           sum(affinita * r2.conteggio) AS punteggio,
           collect(DISTINCT altro.username) AS suggerito_da
    ORDER BY punteggio DESC, brano_consigliato
    """
    stampa(
        f"QUERY 4 - Brani consigliati (filtering collaborativo) per '{utente}'",
        session.run(q4, utente=utente),
    )

    # ----------------------------------------------------------
    # QUERY 5 - Gradi di separazione tra due artisti
    #           (percorso piu' breve nel grafo)
    # ----------------------------------------------------------
    artista_1 = "Maneskin"
    artista_2 = "Adele"
    q5 = """
    MATCH p = shortestPath(
      (a1:Artist {name:$artista_1})
      -[:PUBLISHED|CONTAINS|OF_GENRE|SIMILAR_TO|FOLLOWS|LISTENED*..10]-
      (a2:Artist {name:$artista_2})
    )
    RETURN [n IN nodes(p) | coalesce(n.name, n.title, n.username)] AS percorso,
           length(p) AS gradi_di_separazione
    """
    stampa(
        f"QUERY 5 - Gradi di separazione tra '{artista_1}' e '{artista_2}'",
        session.run(q5, artista_1=artista_1, artista_2=artista_2),
    )

    # ----------------------------------------------------------
    # QUERY 6 - Brani consigliati per SIMILARITA'
    #           (sfrutta SIMILAR_TO.{stile, atmosfera, strumenti})
    #           Dai brani piu' ascoltati, segue gli archi SIMILAR_TO
    #           (freccia orientata -> per non duplicare le coppie) e
    #           ordina per punteggio combinato (media delle 3 dimensioni).
    # ----------------------------------------------------------
    q6 = """
    MATCH (u:User {username:$utente})-[l:LISTENED]->(seed:Track)
    WITH u, seed, l.conteggio AS riproduzioni
    ORDER BY riproduzioni DESC
    LIMIT 10
    MATCH (seed)-[s:SIMILAR_TO]->(cand:Track)
    WHERE NOT (u)-[:LISTENED]->(cand)
    WITH cand, seed, (s.stile + s.atmosfera + s.strumenti) / 3.0 AS score_combinato
    WITH cand, round(max(score_combinato), 2) AS similarita,
         collect(DISTINCT seed.title) AS simile_a
    RETURN cand.title AS brano_consigliato, similarita, simile_a
    ORDER BY similarita DESC, brano_consigliato
    """
    stampa(
        f"QUERY 6 - Brani simili consigliati per '{utente}' (score combinato)",
        session.run(q6, utente=utente),
    )

    # ----------------------------------------------------------
    # QUERY 6-bis - Variante filtrata su UNA dimensione (atmosfera > 0.6)
    # ----------------------------------------------------------
    q6b = """
    MATCH (u:User {username:$utente})-[:LISTENED]->(seed:Track)
          -[s:SIMILAR_TO]->(cand:Track)
    WHERE NOT (u)-[:LISTENED]->(cand) AND s.atmosfera > 0.6
    RETURN DISTINCT cand.title AS brano_consigliato,
           s.atmosfera AS atmosfera, s.stile AS stile, s.strumenti AS strumenti,
           seed.title AS simile_a
    ORDER BY atmosfera DESC, brano_consigliato
    """
    stampa(
        f"QUERY 6-bis - Brani simili per ATMOSFERA (>0.6) per '{utente}'",
        session.run(q6b, utente=utente),
    )

    # ----------------------------------------------------------
    # QUERY 7 - Ascolti recenti (sfrutta LISTENED.timestamp)
    #           Ultimi 6 mesi rispetto all'ascolto piu' recente nel DB.
    # ----------------------------------------------------------
    q7 = """
    MATCH (:User)-[r0:LISTENED]->(:Track)
    WITH max(r0.timestamp) AS ultimo
    MATCH (u:User {username:$utente})-[r:LISTENED]->(t:Track)
    WHERE r.timestamp >= ultimo - duration({months:6})
    RETURN t.title AS brano, r.conteggio AS riproduzioni,
           toString(r.timestamp) AS quando
    ORDER BY r.timestamp DESC
    """
    stampa(
        f"QUERY 7 - Ascolti recenti (ultimi 6 mesi) di '{utente}'",
        session.run(q7, utente=utente),
    )

    session.close()
    driver.close()


if __name__ == "__main__":
    main()
