// ------------------------------------------------------------
// QUERY 1
// Trovare brani consigliati a un utente in base agli artisti che segue e ai generi che ascolta di piu'.
//   - punteggio +2 se il brano e' di un artista seguito
//   - punteggio +1 per ogni genere preferito del brano
//   - si escludono i brani gia' ascoltati
// ------------------------------------------------------------
MATCH (u:User {username:'Marco'})-[r:LISTENED]->(:Track)-[:OF_GENRE]->(g:Genre)
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
// Individuare artisti collegati indirettamente perche' ascoltati dagli stessi gruppi di utenti.
// Due artisti sono collegati se esistono utenti che hanno ascoltato brani di entrambi.
// ------------------------------------------------------------
MATCH (a1:Artist)-[:PUBLISHED]->(:Album)-[:CONTAINS]->(:Track)<-[:LISTENED]-(u:User)-[:LISTENED]->(:Track)<-[:CONTAINS]-(:Album)<-[:PUBLISHED]-(a2:Artist)
WHERE a1.name < a2.name
RETURN a1.name AS artista_1,
       a2.name AS artista_2,
       count(DISTINCT u) AS ascoltatori_comuni
ORDER BY ascoltatori_comuni DESC, artista_1, artista_2;


// ------------------------------------------------------------
// QUERY 3
// Dato un utente, mostrare gli artisti a 2 hop di distanza secondo la logica:
//     Utente -> Artista <- Utente -> Artista
// ------------------------------------------------------------
MATCH (u:User {username:'Marco'})-[:FOLLOWS]->(:Artist)
      <-[:FOLLOWS]-(altro:User)-[:FOLLOWS]->(a2:Artist)
WHERE NOT (u)-[:FOLLOWS]->(a2)
RETURN a2.name AS artista_consigliato,
       count(DISTINCT altro) AS tramite_n_utenti
ORDER BY tramite_n_utenti DESC, artista_consigliato;


// ------------------------------------------------------------
// QUERY 4
// Consigliare brani a un utente in base agli altri utenti che hanno ascoltato i suoi stessi brani (filtering collaborativo).
//   - l'affinita' e' il numero di brani ascoltati in comune
//   - ogni altro utente "vota" i propri brani con la sua affinita'
//   - si escludono i brani gia' ascoltati dall'utente
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
// Calcolare i "gradi di separazione" tra due artisti trovando il percorso piu' breve nel grafo, attraverso qualsiasi relazione (pubblicazioni, generi, similarita', follow, ascolti).
// ------------------------------------------------------------
MATCH p = shortestPath(
  (a1:Artist {name:'Maneskin'})
  -[:PUBLISHED|CONTAINS|OF_GENRE|SIMILAR_TO|FOLLOWS|LISTENED*..10]-
  (a2:Artist {name:'Adele'})
)
RETURN [n IN nodes(p) | coalesce(n.name, n.title, n.username)] AS percorso,
       length(p) AS gradi_di_separazione;