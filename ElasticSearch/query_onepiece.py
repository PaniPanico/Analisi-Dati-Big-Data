"""
============================================================
 DB NoSQL DOCUMENTALE (Elasticsearch) - Tema: One Piece
 Script Python: crea l'indice, carica i dati ed esegue le query.
============================================================

Prerequisiti:
  - Elasticsearch in esecuzione su http://localhost:9200
    (vedi ISTRUZIONI_ELASTIC.txt - si avvia con docker compose)
  - pip install elasticsearch

Esecuzione:
    python query_onepiece.py            # esegue le query
    python query_onepiece.py --carica   # (ri)crea indice e dati

NB: per usare i tasti --carica e' necessario il file bulk.ndjson
    nella stessa cartella.
"""

import json
import os
import sys
from elasticsearch import Elasticsearch, helpers

INDEX = "one_piece"
es = Elasticsearch("http://localhost:9200")

MAPPING = {
    "mappings": {
        "properties": {
            "name":        {"type": "text"},
            "crew":        {"type": "keyword"},
            "origin":      {"type": "keyword"},
            "bounty":      {"type": "long"},
            "devil_fruit": {"type": "keyword"},
            "role":        {"type": "keyword"},
            "status":      {"type": "keyword"},
            "description": {"type": "text"},
        }
    }
}


def carica_dati():
    """Crea l'indice (cancellandolo se esiste) e carica bulk.ndjson."""
    if es.indices.exists(index=INDEX):
        es.indices.delete(index=INDEX)
    es.indices.create(index=INDEX, body=MAPPING)

    base = os.path.dirname(__file__)
    azioni = []
    with open(os.path.join(base, "bulk.ndjson"), "r", encoding="utf-8") as f:
        righe = [r for r in f if r.strip()]
    # le righe sono a coppie: { "index": {...} } seguita dal documento
    for i in range(0, len(righe), 2):
        meta = json.loads(righe[i])["index"]
        doc = json.loads(righe[i + 1])
        azioni.append({"_index": INDEX, "_id": meta["_id"], "_source": doc})
    helpers.bulk(es, azioni)
    es.indices.refresh(index=INDEX)
    print(f"Indice '{INDEX}' creato con {len(azioni)} documenti.\n")


def stampa_hits(titolo, risultato):
    print("=" * 60)
    print(titolo)
    print("-" * 60)
    print("Risultati trovati:", risultato["hits"]["total"]["value"])
    for hit in risultato["hits"]["hits"]:
        s = hit["_source"]
        taglia = f"{s['bounty']:,}" if "bounty" in s else "n/d"
        print(f"  - {s['name']} ({s.get('crew','')}) | taglia: {taglia}")
    print()


def stampa_highlight(risultato):
    """Stampa i frammenti evidenziati (highlight) di ogni hit, se presenti."""
    for hit in risultato["hits"]["hits"]:
        hl = hit.get("highlight")
        if not hl:
            continue
        nome = hit["_source"].get("name", hit["_id"])
        for campo, frammenti in hl.items():
            for frammento in frammenti:
                print(f"    * [{nome}] {campo}: {frammento}")
    print()


def main():
    if "--carica" in sys.argv or not es.indices.exists(index=INDEX):
        carica_dati()

    # ----------------------------------------------------------
    # 1) FULL-TEXT SEARCH: multi_match fuzzy su name + description
    #    Cerca "Zorro swordsman" tollerando errori di battitura
    #    (fuzziness AUTO) e dando piu' peso al campo 'name' (^3).
    #    Gli highlight mostrano i termini che hanno fatto match.
    # ----------------------------------------------------------
    res = es.search(
        index=INDEX,
        size=5,
        query={
            "multi_match": {
                "query": "Zorro swordsman",
                "fields": ["name^3", "description"],
                "fuzziness": "AUTO",
            }
        },
        highlight={"fields": {"name": {}, "description": {}}},
    )
    stampa_hits("1) Full-text: multi_match fuzzy 'Zorro swordsman'", res)
    stampa_highlight(res)

    # ----------------------------------------------------------
    # 2) FILTRO: membri della ciurma di Cappello di Paglia
    #    (nel dataset reale: 'Straw Hat Pirates')
    # ----------------------------------------------------------
    res = es.search(
        index=INDEX,
        query={"term": {"crew": "Straw Hat Pirates"}},
        sort=[{"bounty": "desc"}],
        size=20,
    )
    stampa_hits("2) Filtro: ciurma di Cappello di Paglia (Straw Hat Pirates)", res)

    # ----------------------------------------------------------
    # 3) RANGE: taglia superiore a 1 miliardo
    # ----------------------------------------------------------
    res = es.search(
        index=INDEX,
        query={"range": {"bounty": {"gt": 1000000000}}},
        sort=[{"bounty": "desc"}],
        size=20,
    )
    stampa_hits("3) Range: taglia superiore a 1.000.000.000 berry", res)

    # ----------------------------------------------------------
    # 4) AGGREGAZIONE: taglia media per ciurma
    # ----------------------------------------------------------
    res = es.search(
        index=INDEX,
        size=0,
        aggs={
            "per_ciurma": {
                "terms": {"field": "crew", "size": 20},
                "aggs": {"taglia_media": {"avg": {"field": "bounty"}}},
            }
        },
    )
    print("=" * 60)
    print("4) Aggregazione: taglia media per ciurma")
    print("-" * 60)
    for b in res["aggregations"]["per_ciurma"]["buckets"]:
        media = b["taglia_media"]["value"] or 0
        print(f"  - {b['key']}: {b['doc_count']} membri | media {media:,.0f} berry")
    print()


if __name__ == "__main__":
    main()
