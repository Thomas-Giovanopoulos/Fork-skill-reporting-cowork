-- ============================================================================
-- Migration 003 — D44 : purger les payloads DÉJÀ CHARGÉS en base
-- ============================================================================
--   docker exec rhetores-dev-db psql -U rhetores -d rhetores_ref -v ON_ERROR_STOP=1 \
--       -f /tmp/migration_003_purge_payloads.sql
--
-- Rejouable : ce ne sont que des UPDATE idempotents, valeur pour valeur.
--
-- ---------------------------------------------------------------------------
-- POURQUOI CETTE MIGRATION EXISTE — une purge partielle, la troisième
-- ---------------------------------------------------------------------------
-- La migration 002 a traité `acteur_successions.contexte` et `adjudications.source_document`,
-- parce que c'étaient les deux seules fuites identifiées à l'heure où elle a été écrite. Les
-- fuites de `payload` ont été trouvées APRÈS, et corrigées **dans le seed seulement**.
--
-- Or la base avait été chargée AVANT cette correction. Résultat, constaté en relisant un
-- `ref_bundle` réel : la base servait encore à CHAQUE CGP un numéro de contrat client dans cinq
-- payloads d'acteurs, un second dans un sixième, et quatre noms de clients dans des notes de
-- provenance. La source était propre, la donnée déployée ne l'était pas.
--
-- C'est la même erreur que les deux fois précédentes, à un autre étage : **un constat de fuite
-- oblige à balayer la CATÉGORIE, pas l'occurrence** — et « la catégorie » inclut les copies déjà
-- déployées, pas seulement le fichier source.
--
-- ---------------------------------------------------------------------------
-- POURQUOI DES UPDATE ET NON UN RECHARGEMENT DE seed.sql
-- ---------------------------------------------------------------------------
-- `seed.sql` est idempotent pour les acteurs, les gabarits et les ISIN (`ON CONFLICT DO UPDATE`),
-- mais **pas pour les successions** : leur INSERT n'a aucune cible de conflit, faute de clé
-- naturelle. Un rechargement complet créerait donc des successions en DOUBLE. D'où des UPDATE
-- ciblés.
--
-- Et ces UPDATE sont **générés depuis le seed purgé**, pas écrits à la main : recopier des JSON
-- de plusieurs lignes à la main est précisément le geste qui fait diverger la base de sa source.
--
-- ⚠️ Cette migration écrase `payload` en entier. Si une adjudication a enrichi un payload depuis
--    le chargement, l'enrichissement est perdu. Au 2026-07-29 aucune ne l'a fait — la seule
--    adjudication acceptée portait sur `gabarits`, table non touchée ici.
-- ============================================================================

SET search_path TO ref, public;

BEGIN;

UPDATE acteurs SET payload = '{"libelle_affichage": "De Pury Pictet", "convention": "Écrire « De Pury Pictet ». Jamais « PPT », jamais le nom complet avec Turrettini.", "source": "relevé d''évaluation de portefeuille sous mandat — pied de page présent sur 100 % des pages"}'::jsonb
 WHERE code = 'de_pury_pictet';

UPDATE acteurs SET payload = '{"agrement_amf": "GP-17000033", "adresse": "18bis rue d''Anjou, 75008 Paris", "note": "Société de gestion du groupe. Publie aussi un commentaire de marché hebdomadaire, source du bloc Contexte.", "source": "reportings hebdomadaires de gestion sous mandat (3 au corpus)"}'::jsonb
 WHERE code = 'dauphine_am';

UPDATE acteurs SET payload = '{"note": "Émetteur réel des relevés distribués sous la marque UAF Life Patrimoine. Émetteur ≠ distributeur (D24).", "source": "deux relevés « UAF » du corpus, même gabarit — mentions légales SPIRICA"}'::jsonb
 WHERE code = 'spirica';

UPDATE acteurs SET payload = '{"note": "Distributeur, PAS l''émetteur du relevé. Les relevés nommés « UAF » sont émis par Spirica.", "emetteurs_associes": ["spirica"]}'::jsonb
 WHERE code = 'uaf_life_patrimoine';

UPDATE acteurs SET payload = '{"note": "Plateforme grossiste, PAS un assureur. Son nom n''apparaît NULLE PART dans le texte du relevé : l''identité est portée par un logo image. Nommé par un humain, jamais déduit au runtime (D24/N7).", "identifie_par": "logo image, non OCR — le nom de fichier ne fait pas foi", "source": "relevé « Nortia 30 06 26 »"}'::jsonb
 WHERE code = 'nortia';

UPDATE acteurs SET payload = '{"note": "L''assureur n''est identifiable NI dans le texte NI par une source fiable de ce run. Un nom plausible circule mais n''est pas vérifié : il n''est pas inscrit ici. À faire nommer par le CGP (AskUser), au même titre que K7.", "question_ouverte": "Quel assureur porte la gamme HIMALIA CAPITALISATION ?", "identifie_par": "logo image, non OCR"}'::jsonb
 WHERE code = 'himalia_emetteur_a_confirmer';

UPDATE acteurs SET payload = '{"rcs": "Luxembourg B 53682", "tva": "LU 166 094 20", "adresse": "12 rue Léon Laval, L-3372 Leudelange", "note": "Assurance-vie luxembourgeoise : le triangle de sécurité impose un dépositaire tiers nommé par fonds dédié (FID). Un contrat peut donc porter PLUSIEURS dépositaires, et ils changent dans le temps (voir successions).", "source": "deux relevés annuels du même émetteur"}'::jsonb
 WHERE code = 'wealins';

UPDATE acteurs SET payload = '{"note": "Contrat FR : pas de dépositaire tiers, la colonne dépositaire vaut NC par convention réglementaire — « non communicable », pas « non renseigné » (D26).", "reseau_declare": "DIRECT-CGPI", "source": "relevé Cardif Elite Capitalisation Personnes Morales"}'::jsonb
 WHERE code = 'cardif';

UPDATE acteurs SET payload = '{"note": "Dépositaire d''un FID Wealins. Successeur de CIC sur la poche FID d''un contrat Wealins observé au corpus."}'::jsonb
 WHERE code = 'quintet';

UPDATE acteurs SET payload = '{"note": "Dépositaire d''un FID Wealins. Successeur d''Intesa sur la poche FAS d''un contrat Wealins observé au corpus.", "question_ouverte": "K7 — CA Indosuez et Banque Thaler sont-ils la même entité, ou deux repreneurs distincts de la poche ex-Intesa ? Le salvage ne permet pas de trancher. AskUser au CGP."}'::jsonb
 WHERE code = 'ca_indosuez';

UPDATE acteurs SET payload = '{"note": "Apparaît comme dépositaire d''un FID d''un contrat Wealins observé au corpus. Relation avec CA Indosuez non établie — voir K7.", "question_ouverte": "K7 (identique à ca_indosuez)"}'::jsonb
 WHERE code = 'banque_thaler';

UPDATE acteurs SET payload = '{"note": "Prédécesseur sur la poche FAS d''un contrat Wealins. Conservé pour réconcilier les relevés antérieurs au changement (K5)."}'::jsonb
 WHERE code = 'intesa_sanpaolo';

UPDATE acteurs SET payload = '{"note": "Prédécesseur sur la poche FID d''un contrat Wealins. Conservé pour réconcilier les relevés antérieurs (K5)."}'::jsonb
 WHERE code = 'cic';

UPDATE acteurs SET payload = '{"note": "Figure comme « Banque Dépositaire » du mandat De Pury Pictet, et dans DEPO_COLORS du moteur.", "attention": "La valeur lue « UBS Fr » est possiblement tronquée dans le relevé source — ne pas en déduire une entité juridique précise."}'::jsonb
 WHERE code = 'ubs';

UPDATE acteurs SET payload = '{"note": "Présent dans DEPO_COLORS du moteur. Retiré du code au profit de ce référentiel (K4)."}'::jsonb
 WHERE code = 'edmond_de_rothschild';

UPDATE acteurs SET payload = '{"note": "Présent dans DEPO_COLORS du moteur. Retiré du code au profit de ce référentiel (K4)."}'::jsonb
 WHERE code = 'tilvest';

UPDATE acteurs SET payload = '{"note": "Société de gestion de fonds de private equity. Deux fonds observés chez un client, cible 1,8× sur 10 ans, MOIC réels constatés 1,42× et 1,79×.", "rappel_metier": "Le PE représente peu d''actifs à forte importance individuelle : le bloc PE n''a jamais de seuil de pertinence (D32)."}'::jsonb
 WHERE code = 'altaroc';

UPDATE acteur_successions SET payload = '{"note": "Date d''effet non établie par le relevé : laissée à null plutôt que devinée. Une note intermédiaire d''un run réel mentionnait « Thaler/Indosuez » sans permettre de trancher — voir K7.", "question_ouverte": "K7 — le successeur est-il CA Indosuez, Banque Thaler, ou les deux successivement ?", "reperes_chiffres": "Base au 31/12/2024 retenue à 550 568 € dans la version officielle post-relevés ; versement dédié de 250 000 € le 13/03/2025."}'::jsonb,
       contexte = 'reprise de la poche FAS ex-Intesa chez un assureur luxembourgeois'
 WHERE predecesseur_code = 'intesa_sanpaolo'   AND successeur_code = 'ca_indosuez';

UPDATE acteur_successions SET payload = '{"note": "Clôture au 30/12/2025, précision obtenue seulement après lecture des relevés officiels (elle ne figurait pas dans l''Excel de suivi). Date d''effet du changement non établie : laissée à null.", "reperes_chiffres": "Base au 31/12/2024 retenue à 446 933 € dans la version officielle ; versement dédié de 200 000 € le 07/05/2025.", "ecart_de_source": "L''Excel « Catégories & Perf » portait un versement de 251 627 € qui n''existe dans aucun relevé officiel — donnée erronée de la source Excel, corrigée. Illustration de la hiérarchie de sources : le relevé prime."}'::jsonb,
       contexte = 'reprise de la poche FID ex-CIC chez un assureur luxembourgeois'
 WHERE predecesseur_code = 'cic'   AND successeur_code = 'quintet';

COMMIT;

-- ============================================================================
-- Contrôle après migration — le faire, ne pas le supposer
-- ============================================================================
-- Aucune ligne ne doit remonter :
--
--   SELECT code, payload FROM ref.acteurs
--    WHERE payload::text ~* 'FC0[0-9]{5}|Gronier|INTERAGYR|Cerise|Pollux|HANAMI';
--
--   SELECT predecesseur_code, contexte, payload FROM ref.acteur_successions
--    WHERE (contexte || payload::text) ~* 'FC0[0-9]{5}|Gronier|INTERAGYR|Cerise|Pollux|HANAMI';
--
-- Puis relire un `ref_bundle(sections=["acteurs"])` et un `ref_bundle(sections=["successions"])`
-- depuis une session : c'est ce que voit un CGP, et c'est donc le seul contrôle qui compte.
