# One Piece — DB Documentale (Elasticsearch)

Un database **NoSQL documentale** su **Elasticsearch** in cui ogni personaggio di *One Piece* è un
documento JSON autonomo. Il modello valorizza la **ricerca full-text** sulle descrizioni e le **aggregazioni** sulle taglie.

## File del progetto

| File | Contenuto |
|------|-----------|
| `docker-compose.yaml` | Avvia Elasticsearch 8.13 + Kibana. |
| `01_index.txt` | Descrizione del mapping e comando `curl` per creare l'indice. |
| `bulk.ndjson` | Dataset: ~1500 personaggi in formato Bulk API. |
| `query_onepiece.py` | Script Python: crea l'indice, carica i dati ed esegue le query. |
| `presentazione_elasticsearch.html` | Presentazione del progetto. |
| `ISTRUZIONI_ELASTIC.txt` | Guida passo-passo. |

## Il modello dati

Indice `one_piece`, un documento per personaggio:

| Campo | Tipo ES | Descrizione |
|-------|---------|-------------|
| `name` | `text` | nome del personaggio |
| `crew` | `keyword` | ciurma / organizzazione di appartenenza |
| `origin` | `keyword` | mare / luogo di origine |
| `bounty` | `long` | taglia in berry |
| `devil_fruit` | `keyword` | frutto del diavolo (se presente) |
| `role` | `keyword` | ruolo nella ciurma |
| `status` | `keyword` | Alive / Deceased / Unknown |
| `description` | `text` | descrizione testuale |

La distinzione **`text` vs `keyword`** è il cuore del modello: i campi `text`
(`name`, `description`) vengono analizzati e sono adatti alla ricerca full-text;
i campi `keyword` (`crew`, `role`, `status`…) restano esatti e servono a filtri,
ordinamenti e aggregazioni.

## Le query

1. **Full-text search** — `multi_match` su `name` e `description` con
   `fuzziness: AUTO` (tolleranza agli errori di battitura), peso personalizzabile
   (es. `name^3`) ed `highlight` dei termini che hanno fatto match.
2. **Filtro esatto** — `term` sul campo `crew` (es. i membri della ciurma di
   Cappello di Paglia), ordinati per taglia.
3. **Range** — `range` sul campo `bounty` (es. taglia superiore a 1 miliardo).
4. **Aggregazione** — `terms` su `crew` + `avg` su `bounty`: taglia media per
   ciurma.

## Come eseguire

Vedi `ISTRUZIONI_ELASTIC.txt` per i dettagli. In sintesi:

```bash
docker compose up -d              # avvia Elasticsearch + Kibana
pip install elasticsearch
python query_onepiece.py --carica # crea l'indice 'one_piece' e carica i documenti
python query_onepiece.py          # esegue e stampa le query
```

- Elasticsearch risponde su `http://localhost:9200` (JSON con
  `"tagline": "You Know, for Search"`).
- Kibana è disponibile su `http://localhost:5601` (**Dev Tools** per scrivere
  query manualmente).
- Per fermare tutto: `docker compose down` (aggiungi `-v` per cancellare anche i
  dati).

> La presentazione `presentazione_elasticsearch.html` interroga Elasticsearch dal
> vivo dal browser: per questo il `docker-compose.yaml` abilita il **CORS**
> (`http.cors.*`).
