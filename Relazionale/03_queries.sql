-- QUERY 1
-- Elencare tutti i prodotti acquistati da un determinato cliente (esempio: cliente 'Marco Rossi', codice_cliente = 1).

SELECT DISTINCT p.codice_prodotto,
       p.nome,
       cat.nome AS categoria
FROM clienti c
JOIN ordini o        ON c.codice_cliente = o.codice_cliente
JOIN righe_ordine r  ON o.codice_ordine  = r.codice_ordine
JOIN prodotti p      ON r.codice_prodotto = p.codice_prodotto
JOIN categorie cat   ON p.codice_categoria = cat.codice_categoria
WHERE c.codice_cliente = 1
ORDER BY p.nome;

-- QUERY 2
-- Calcolare il totale speso da ciascun cliente.
--   totale riga = quantita * prezzo_applicato

SELECT c.codice_cliente,
       c.nome,
       c.cognome,
       ROUND(SUM(r.quantita * r.prezzo_applicato), 2) AS totale_speso
FROM clienti c
JOIN ordini o       ON c.codice_cliente = o.codice_cliente
JOIN righe_ordine r ON o.codice_ordine  = r.codice_ordine
GROUP BY c.codice_cliente, c.nome, c.cognome
ORDER BY totale_speso DESC;

-- QUERY 3
-- Calcolare la spesa media mensile di ogni cliente per un anno di riferimento (2025).
--
-- Passo 1 (sottoquery): per ogni cliente e per ogni mese in cui ha effettuato ordini si calcola la spesa totale.
-- Passo 2: si fa la media di tali totali mensili.

SELECT m.codice_cliente,
       cl.nome,
       cl.cognome,
       ROUND(AVG(m.totale_mese), 2) AS spesa_media_mensile
FROM (
    SELECT o.codice_cliente,
           strftime('%Y-%m', o.data_ordine)        AS mese,
           SUM(r.quantita * r.prezzo_applicato)     AS totale_mese
    FROM ordini o
    JOIN righe_ordine r ON o.codice_ordine = r.codice_ordine
    WHERE strftime('%Y', o.data_ordine) = '2025'
    GROUP BY o.codice_cliente, mese
) AS m
JOIN clienti cl ON cl.codice_cliente = m.codice_cliente
GROUP BY m.codice_cliente, cl.nome, cl.cognome
ORDER BY spesa_media_mensile DESC;


-- QUERY 4
-- Individuare le coppie di prodotti acquistati piu' spesso insieme (nello stesso ordine).

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
ORDER BY volte_insieme DESC, prodotto_A;

-- QUERY 5
-- Per ogni cliente: data dell'ultimo ordine, giorni di inattivita' (rispetto all'ultimo ordine registrato nel DB)
-- e valore complessivo generato dal cliente. Utile per individuare i clienti da riattivare.

SELECT c.nome || ' ' || c.cognome AS cliente,
       MAX(o.data_ordine) AS ultimo_ordine,
       CAST(julianday((SELECT MAX(data_ordine) FROM ordini))
            - julianday(MAX(o.data_ordine)) AS INT) AS giorni_inattivo,
       ROUND(SUM(r.quantita * r.prezzo_applicato), 2) AS valore_cliente
FROM clienti c
JOIN ordini o       ON c.codice_cliente = o.codice_cliente
JOIN righe_ordine r ON o.codice_ordine  = r.codice_ordine
GROUP BY c.codice_cliente
ORDER BY giorni_inattivo DESC, valore_cliente DESC;
