// ============================================================
//  DB A GRAFO (Neo4j) - Piattaforma musicale
//  Query richieste dalla traccia
// ============================================================

// ------------------------------------------------------------
// QUERY 1
// Trovare brani consigliati a un utente in base agli artisti
// che segue e ai generi che ascolta di piu'.
//   - punteggio +2 se il brano e' di un artista seguito
//   - punteggio +1 per ogni genere preferito del brano
//   - si escludono i brani gia' ascoltati
// (esempio: utente 'Marco')
//
// NOVITA' (prop. LISTENED.conteggio): i generi preferiti ora si pesano
// con la SOMMA DELLE RIPRODUZIONI (sum(r.conteggio)) invece del semplice
// numero di brani ascoltati (count(*)). Cosi' un genere ascoltato poche
// volte ma in modo intensivo pesa piu' di uno con molti brani riprodotti
// una volta sola: il ranking dei generi puo' cambiare rispetto a prima.
// ------------------------------------------------------------
MATCH (u:User {username:'Marco'})
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
RETURN cand.title AS brano_consigliato,
       art.name   AS artista,
       generiBrano AS generi,
       score       AS punteggio
ORDER BY punteggio DESC, brano_consigliato;


// ------------------------------------------------------------
// QUERY 2
// Individuare artisti collegati indirettamente perche'
// ascoltati dagli stessi gruppi di utenti.
//   Due artisti sono collegati se esistono utenti che hanno
//   ascoltato brani di entrambi.
// ------------------------------------------------------------
MATCH (a1:Artist)-[:PUBLISHED]->(:Album)-[:CONTAINS]->(:Track)<-[:LISTENED]-(u:User),
      (u)-[:LISTENED]->(:Track)<-[:CONTAINS]-(:Album)<-[:PUBLISHED]-(a2:Artist)
WHERE a1.name < a2.name
RETURN a1.name AS artista_1,
       a2.name AS artista_2,
       count(DISTINCT u) AS ascoltatori_comuni
ORDER BY ascoltatori_comuni DESC, artista_1, artista_2;


// ------------------------------------------------------------
// QUERY 3
// Dato un utente, mostrare gli artisti a 2 hop di distanza
// secondo la logica:
//     Utente -> Artista <- Utente -> Artista
// (artisti seguiti da chi segue gli stessi artisti dell'utente,
//  escludendo quelli gia' seguiti).
// (esempio: utente 'Marco')
// ------------------------------------------------------------
MATCH (u:User {username:'Marco'})-[:FOLLOWS]->(:Artist)
      <-[:FOLLOWS]-(altro:User)-[:FOLLOWS]->(a2:Artist)
WHERE NOT (u)-[:FOLLOWS]->(a2)
RETURN a2.name AS artista_consigliato,
       count(DISTINCT altro) AS tramite_n_utenti
ORDER BY tramite_n_utenti DESC, artista_consigliato;


// ------------------------------------------------------------
// QUERY 4
// Consigliare brani a un utente in base agli altri utenti che
// hanno ascoltato i suoi stessi brani (filtering collaborativo).
//   - l'affinita' e' il numero di brani ascoltati in comune
//   - ogni altro utente "vota" i propri brani con la sua affinita'
//   - si escludono i brani gia' ascoltati dall'utente
// (esempio: utente 'Marco')
//
// NOVITA' (prop. LISTENED.conteggio): il voto di ogni brano non pesa piu'
// solo per l'affinita' del vicino, ma anche per QUANTE VOLTE il vicino ha
// riprodotto quel brano (affinita * r2.conteggio). Cosi' un brano che un
// utente affine ascolta in modo intensivo sale in classifica rispetto a uno
// che ha ascoltato una volta sola.
// ------------------------------------------------------------
MATCH (me:User {username:'Marco'})-[:LISTENED]->(t:Track)<-[:LISTENED]-(altro:User)
WHERE altro <> me
WITH me, altro, count(DISTINCT t) AS affinita
MATCH (altro)-[r2:LISTENED]->(reco:Track)
WHERE NOT (me)-[:LISTENED]->(reco)
RETURN reco.title AS brano_consigliato,
       sum(affinita * r2.conteggio) AS punteggio,
       collect(DISTINCT altro.username) AS suggerito_da
ORDER BY punteggio DESC, brano_consigliato;


// ------------------------------------------------------------
// QUERY 5
// Calcolare i "gradi di separazione" tra due artisti trovando il
// percorso piu' breve nel grafo, attraverso qualsiasi relazione
// (pubblicazioni, generi, similarita', follow, ascolti).
// (esempio: da 'Maneskin' ad 'Adele')
// ------------------------------------------------------------
MATCH p = shortestPath(
  (a1:Artist {name:'Maneskin'})
  -[:PUBLISHED|CONTAINS|OF_GENRE|SIMILAR_TO|FOLLOWS|LISTENED*..10]-
  (a2:Artist {name:'Adele'})
)
RETURN [n IN nodes(p) | coalesce(n.name, n.title, n.username)] AS percorso,
       length(p) AS gradi_di_separazione;


// ------------------------------------------------------------
// QUERY 6  (NUOVA - sfrutta SIMILAR_TO.{stile, atmosfera, strumenti})
// Brani consigliati per SIMILARITA': dai brani piu' ascoltati
// dall'utente si seguono gli archi SIMILAR_TO verso brani non ancora
// ascoltati, ordinati per un punteggio di similarita' COMBINATO
// (media delle tre dimensioni). Prima i candidati "simili" non erano
// nemmeno esprimibili (arco nudo, nessun punteggio); ora il ranking
// e' guidato dai valori sull'arco.
//
// ATTENZIONE AI DUPLICATI: SIMILAR_TO e' materializzato in ENTRAMBE le
// direzioni. Usiamo la FRECCIA ORIENTATA (seed)-[s]->(cand) cosi' ogni
// coppia (brano ascoltato -> candidato) compare una sola volta.
// (esempio: utente 'Marco')
// ------------------------------------------------------------
MATCH (u:User {username:'Marco'})-[l:LISTENED]->(seed:Track)
WITH u, seed, l.conteggio AS riproduzioni
ORDER BY riproduzioni DESC
LIMIT 10                                   // si parte dai 10 brani piu' ascoltati
MATCH (seed)-[s:SIMILAR_TO]->(cand:Track)
WHERE NOT (u)-[:LISTENED]->(cand)
WITH cand, seed,
     (s.stile + s.atmosfera + s.strumenti) / 3.0 AS score_combinato
WITH cand,
     round(max(score_combinato), 2) AS similarita,      // la migliore affinita'
     collect(DISTINCT seed.title)   AS simile_a
RETURN cand.title AS brano_consigliato,
       similarita,
       simile_a
ORDER BY similarita DESC, brano_consigliato;


// ------------------------------------------------------------
// QUERY 6-bis  (VARIANTE su UNA sola dimensione)
// Stessa idea, ma filtrando i candidati per una singola dimensione:
// qui solo i brani con forte affinita' di ATMOSFERA (> 0.6).
// Basta cambiare la proprieta' nel WHERE per filtrare su stile o strumenti.
// ------------------------------------------------------------
MATCH (u:User {username:'Marco'})-[:LISTENED]->(seed:Track)
      -[s:SIMILAR_TO]->(cand:Track)
WHERE NOT (u)-[:LISTENED]->(cand)
  AND s.atmosfera > 0.6
RETURN DISTINCT cand.title AS brano_consigliato,
       s.atmosfera AS atmosfera,
       s.stile     AS stile,
       s.strumenti AS strumenti,
       seed.title  AS simile_a
ORDER BY atmosfera DESC, brano_consigliato;


// ------------------------------------------------------------
// QUERY 7  (NUOVA - sfrutta LISTENED.timestamp)
// Ascolti recenti di un utente: i brani ascoltati negli ultimi 6 mesi,
// dal piu' recente. Il riferimento temporale e' l'ascolto piu' recente
// presente nel DB (non datetime() di sistema), cosi' la query resta
// significativa a prescindere dalla data in cui viene eseguita.
// (esempio: utente 'Marco')
// ------------------------------------------------------------
MATCH (:User)-[r0:LISTENED]->(:Track)
WITH max(r0.timestamp) AS ultimo
MATCH (u:User {username:'Marco'})-[r:LISTENED]->(t:Track)
WHERE r.timestamp >= ultimo - duration({months:6})
RETURN t.title            AS brano,
       r.conteggio        AS riproduzioni,
       toString(r.timestamp) AS quando
ORDER BY r.timestamp DESC;
