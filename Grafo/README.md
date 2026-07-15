# Piattaforma musicale - DB a Grafo (Neo4j)

Un **knowledge graph** su Neo4j che modella una
piattaforma di streaming musicale (artisti, album, brani, generi, utenti e
playlist) e la interroga per **consigliare musica**, scoprire **affinità** tra
artisti e misurare i **gradi di separazione** nel grafo.

## File del progetto

| File | Contenuto |
|------|-----------|
| `01_create.cypher` | Crea l'intero grafo (nodi + relazioni). Parte con `MATCH (n) DETACH DELETE n;` per ripartire da zero. |
| `02_queries.cypher` | Le query in Cypher da incollare su Neo4j. |
| `query_musica.py` | Script Python che si connette a Neo4j ed esegue le query. |
| `presentazione.html` | Presentazione del progetto. |
| `ISTRUZIONI_NEO4J.txt` | Guida passo-passo. |

## Il modello dati

Sei tipi di nodo e otto tipi di relazione. **Due relazioni portano proprietà sugli archi**: `LISTENED` e `SIMILAR_TO`.

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

- **`LISTENED.conteggio`** - quante volte l'utente ha riprodotto quel brano.
  Valori alti (10–40) per i brani del genere preferito, bassi (1–3) per gli
  ascolti sporadici.
- **`LISTENED.timestamp`** - data/ora dell'ultimo ascolto.
- **`SIMILAR_TO`** - la similarità è **simmetrica**: l'arco è materializzato in
  entrambe le direzioni `A→B` e `B→A` con **valori identici**. Le tre dimensioni:
  - `stile` - vicinanza di stile;
  - `atmosfera` - affinità di mood;
  - `strumenti` - somiglianza degli strumenti predominanti.

## Le query

`02_queries.cypher` e `query_musica.py` contengono:

1. **Consigli su misura** - brani consigliati in base agli artisti seguiti
   e ai **generi più ascoltati** dell'utente.
2. **Artisti affini per pubblico** - coppie di artisti ascoltati dagli stessi utenti.
3. **Rete di gusti (2 hop)** - `Utente → Artista ← Utente → Artista`.
4. **Filtering collaborativo** - “gli utenti come te hanno ascoltato anche…”.
   Il voto di ogni brano pesa per l'affinità del vicino **e** per le sue
   riproduzioni (`affinita * r2.conteggio`).
5. **Gradi di separazione** - `shortestPath` tra due artisti.

## Come eseguire

Vedi `ISTRUZIONI_NEO4J.txt` per i dettagli. In sintesi:

1. Avvia Neo4j Desktop e crea/avvia un DBMS locale.
2. Carica i dati: incolla `01_create.cypher` nel Neo4j Browser **oppure** lancia
   `python query_musica.py --crea`.
3. Esegui le query: `python query_musica.py`, oppure incolla le query di
   `02_queries.cypher` nel Browser, oppure apri `presentazione.html` e premi **Connetti**.