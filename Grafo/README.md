# Piattaforma musicale — DB a Grafo (Neo4j)

Progetto d'esame *Big Data*: un **knowledge graph** su Neo4j che modella una
piattaforma di streaming musicale (artisti, album, brani, generi, utenti e
playlist) e la interroga per **consigliare musica**, scoprire **affinità** tra
artisti e misurare i **gradi di separazione** nel grafo.

## File del progetto

| File | Contenuto |
|------|-----------|
| `01_create.cypher` | Crea l'intero grafo (nodi + relazioni). Parte con `MATCH (n) DETACH DELETE n;` per ripartire da zero. |
| `02_queries.cypher` | Le query Cypher richieste dalla traccia, da incollare nel Neo4j Browser. |
| `query_musica.py` | Script Python che si connette a Neo4j ed esegue le stesse query. |
| `presentazione.html` | Presentazione interattiva: esegue le query **dal vivo** sul database. |
| `ISTRUZIONI_NEO4J.txt` | Guida passo-passo all'installazione e al caricamento dei dati. |

## Il modello dati

Sei tipi di nodo e otto tipi di relazione. **Due relazioni portano proprietà
sugli archi**: `LISTENED` e `SIMILAR_TO`.

```
        PUBLISHED           CONTAINS            OF_GENRE
 Artist ──────────► Album ──────────► Track ──────────► Genre
   ▲                                   │  ▲
   │ FOLLOWS                SIMILAR_TO │  │ LISTENED {conteggio, timestamp}
   │                    {stile,        └──┘
 User ─── LISTENED ────► atmosfera,       │
   │                     strumenti}       │
   │ CREATED                              │
   ▼                    INCLUDES          │
 Playlist ─────────────────────────────► Track
```

### Nodi

| Nodo | Proprietà | Quantità |
|------|-----------|----------|
| `:Artist` | `name`, `country`, `debut_year` | 40 |
| `:Album` | `title`, `year` | 114 |
| `:Track` | `title`, `duration` (secondi) | 301 |
| `:Genre` | `name` | 18 |
| `:User` | `username` | 35 |
| `:Playlist` | `name` | 10 |

### Relazioni

| Relazione | Da → A | Proprietà | Note |
|-----------|--------|-----------|------|
| `PUBLISHED` | Artist → Album | — | |
| `CONTAINS` | Album → Track | — | |
| `OF_GENRE` | Track → Genre | — | un brano può avere più generi |
| `FOLLOWS` | User → Artist | — | 163 archi |
| `CREATED` | User → Playlist | — | |
| `INCLUDES` | Playlist → Track | — | |
| **`LISTENED`** | User → Track | **`conteggio`** (int ≥ 1), **`timestamp`** (datetime) | 389 archi. Numero di riproduzioni e data/ora dell'ultimo ascolto. I conteggi alti si concentrano sui generi preferiti di ciascun utente. |
| **`SIMILAR_TO`** | Track → Track | **`stile`**, **`atmosfera`**, **`strumenti`** (float ∈ [0,1]) | 78 archi (39 coppie). Punteggi di similarità su tre dimensioni. |

#### Dettaglio delle proprietà sugli archi

- **`LISTENED.conteggio`** — quante volte l'utente ha riprodotto quel brano.
  Valori alti (10–40) per i brani del genere preferito, bassi (1–3) per gli
  ascolti sporadici: serve a pesare correttamente i gusti.
- **`LISTENED.timestamp`** — data/ora dell'ultimo ascolto, distribuita sugli
  ultimi ~24 mesi.
- **`SIMILAR_TO`** — la similarità è **simmetrica**: l'arco è materializzato in
  entrambe le direzioni `A→B` e `B→A` con **valori identici**. Le tre dimensioni:
  - `stile` — vicinanza di stile (alta tra brani dello stesso artista/genere,
    bassa nei “ponti” tra generi diversi);
  - `atmosfera` — affinità di mood, può essere alta anche fra generi diversi
    (es. un brano electronic e uno soul);
  - `strumenti` — somiglianza degli strumenti predominanti.

## Le query

`02_queries.cypher` e `query_musica.py` contengono:

1. **Consigli su misura** — brani consigliati in base agli artisti seguiti (+2)
   e ai **generi più ascoltati** dell'utente. I generi preferiti sono pesati con
   `sum(r.conteggio)` (riproduzioni), non più con `count(*)`: un genere ascoltato
   in modo intensivo pesa di più di uno con molti brani riprodotti una volta sola.
2. **Artisti affini per pubblico** — coppie di artisti ascoltati dagli stessi utenti.
3. **Rete di gusti (2 hop)** — `Utente → Artista ← Utente → Artista`.
4. **Filtering collaborativo** — “gli utenti come te hanno ascoltato anche…”.
   Il voto di ogni brano pesa per l'affinità del vicino **e** per le sue
   riproduzioni (`affinita * r2.conteggio`).
5. **Gradi di separazione** — `shortestPath` tra due artisti.
6. **Brani simili** *(nuova, usa `SIMILAR_TO`)* — dai brani più ascoltati
   dall'utente segue gli archi `SIMILAR_TO` verso brani non ancora ascoltati,
   ordinati per punteggio **combinato** (media di stile/atmosfera/strumenti).
   La variante *6-bis* filtra su **una sola dimensione** (es. `atmosfera > 0.6`).
   Si usa la **freccia orientata** `(seed)-[:SIMILAR_TO]->(cand)` per non contare
   due volte le coppie (l'arco è bidirezionale).
7. **Ascolti recenti** *(nuova, usa `timestamp`)* — i brani ascoltati negli
   ultimi 6 mesi, dal più recente.

## Come eseguire

Vedi `ISTRUZIONI_NEO4J.txt` per i dettagli. In sintesi:

1. Avvia Neo4j Desktop e crea/avvia un DBMS locale.
2. Carica i dati: incolla `01_create.cypher` nel Neo4j Browser **oppure** lancia
   `python query_musica.py --crea`.
3. Esegui le query: `python query_musica.py`, oppure incolla le query di
   `02_queries.cypher` nel Browser, oppure apri `presentazione.html` (servita da
   `http://localhost`, non `https`) e premi **Connetti**.

> Nota: per un'immagine dello schema dal Browser, esegui
> `MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100` e usa l'export PNG del pannello grafo.
