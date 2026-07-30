-- ============================================================================
-- Migration 001 — D42 : fenêtre de validité des gabarits, périodicité hors clé
-- ============================================================================
-- À jouer sur une base DÉJÀ CRÉÉE par ddl_referentiels_v0.sql. Le DDL a été mis à jour
-- en parallèle pour les installations neuves : cette migration ne sert qu'aux bases
-- existantes — celle de Thomas, exécutée le 2026-07-29.
--
--   docker exec rhetores-dev-db psql -U rhetores -d rhetores_ref -v ON_ERROR_STOP=1 \
--       -f /tmp/migration_001_d42_fenetre_validite.sql
--
-- Rejouable : chaque étape est gardée par un test d'existence.
--
-- ---------------------------------------------------------------------------
-- POURQUOI — deux motifs, tirés du corpus du 2026-07-29
-- ---------------------------------------------------------------------------
-- (a) La périodicité n'est PAS LISIBLE dans le document chez trois émetteurs sur quatre.
--     « trimestriels » chez Spirica désigne une offre commerciale ; « pour l'année » chez
--     Cardif une fenêtre de cumul YTD, inchangée sur des arrêtés au 30/03 et au 30/06 ;
--     Himalia n'a aucun token (« 8 années » est la durée du contrat). Une clé d'appariement
--     ne peut pas reposer sur une valeur indéterminable à la lecture : la périodicité devient
--     informative, renseignée par le contexte du run.
--
-- (b) Un émetteur change de maquette. Cardif a produit deux gabarits en douze mois, et une
--     seule ancre sur onze survit de l'un à l'autre. Sans fenêtre de validité, le nouveau
--     format ÉCRASE l'ancien et les relevés archivés deviennent inparsables — or le run
--     Gronier lit des relevés jusqu'à 2022. À l'inverse, Himalia n'a pas bougé en treize mois
--     (30 ancres sur 30, bbox au centième de point) : imposer un versionnement partout serait
--     du bruit. La fenêtre est donc une CAPACITÉ, pas une règle.
--
-- ---------------------------------------------------------------------------
-- LE PIÈGE QUI JUSTIFIE LE `NOT NULL` — à ne pas « simplifier » plus tard
-- ---------------------------------------------------------------------------
-- La tentation était de laisser `valide_depuis` nullable, NULL signifiant « depuis toujours ».
-- C'est un défaut, pour une raison qui ne se voit qu'à l'exécution : en SQL, **deux NULL sont
-- distincts dans une contrainte d'unicité**. Deux profils (cardif, situation_contrat_capi_pm,
-- NULL) auraient donc été acceptés tous les deux — l'unicité ne protégeait plus rien.
--
-- Pire, et c'est le vrai danger : `ref_arbitrer` écrit par `INSERT ... ON CONFLICT (clé) DO
-- UPDATE`. Une cible de conflit contenant un NULL ne matche jamais : chaque adjudication
-- acceptée aurait **inséré un doublon** au lieu de mettre à jour, silencieusement, et
-- `ref_bundle` aurait rendu plusieurs profils pour le même gabarit.
--
-- D'où la convention : `valide_depuis NOT NULL DEFAULT '0001-01-01'`, cette date signifiant
-- « depuis toujours ». Aucun NULL, l'unicité tient, l'UPSERT fonctionne. On préfère cela à
-- `UNIQUE NULLS NOT DISTINCT` (PostgreSQL 15+) : la convention de date ne dépend d'aucune
-- version, et elle se lit dans les données.
-- ============================================================================

SET search_path TO ref, public;

BEGIN;

-- 1 — Les deux bornes de la fenêtre --------------------------------------------------------
-- '0001-01-01' = « depuis toujours ». `valide_jusqu_a` reste nullable : NULL y signifie
-- « toujours en cours », et il ne participe à aucune contrainte d'unicité.
ALTER TABLE gabarits
    ADD COLUMN IF NOT EXISTS valide_depuis  date NOT NULL DEFAULT '0001-01-01',
    ADD COLUMN IF NOT EXISTS valide_jusqu_a date;

COMMENT ON COLUMN gabarits.valide_depuis IS
    'Début de validité du gabarit. ''0001-01-01'' = depuis toujours. NOT NULL à dessein : '
    'un NULL casserait l''unicité (deux NULL sont distincts) et ferait insérer des doublons '
    'par l''ON CONFLICT de ref_arbitrer. Cf. migration_001.';
COMMENT ON COLUMN gabarits.valide_jusqu_a IS
    'Fin de validité, NULL = toujours en cours. Sert à CHOISIR entre versions, jamais à '
    'retirer un profil : un ancien gabarit doit rester lisible pour parser les archives '
    '(le run Gronier remonte à 2022). Limite L5 de l''étude de corpus.';

-- 2 — Cohérence de la fenêtre --------------------------------------------------------------
ALTER TABLE gabarits DROP CONSTRAINT IF EXISTS gabarit_fenetre_coherente;
ALTER TABLE gabarits ADD CONSTRAINT gabarit_fenetre_coherente
    CHECK (valide_jusqu_a IS NULL OR valide_jusqu_a >= valide_depuis);

-- 3 — La clé d'unicité change ---------------------------------------------------------------
-- `periodicite` sort de la clé, `valide_depuis` y entre. Le nom de la nouvelle contrainte
-- diffère de l'ancienne : `_upsert_canonique` cible les COLONNES et non le nom, donc rien
-- à changer côté MCP — mais la liste de colonnes du `conflict` de tools/referentiels.py
-- doit être mise à jour dans le même mouvement, sinon l'UPSERT échoue à l'exécution.
ALTER TABLE gabarits DROP CONSTRAINT IF EXISTS gabarit_couple_unique;
ALTER TABLE gabarits DROP CONSTRAINT IF EXISTS gabarit_version_unique;
ALTER TABLE gabarits ADD CONSTRAINT gabarit_version_unique
    UNIQUE (emetteur_code, gabarit, valide_depuis);

-- 4 — La périodicité devient informative ----------------------------------------------------
-- Elle n'est plus discriminante, donc plus obligatoire. On ne la SUPPRIME pas : quand elle est
-- connue (Wealins l'inscrit dans son en-tête d'annexe), c'est une information utile au CGP.
ALTER TABLE gabarits ALTER COLUMN periodicite DROP NOT NULL;
COMMENT ON COLUMN gabarits.periodicite IS
    'INFORMATIVE, hors matching (D42). Non lisible dans le document chez 3 émetteurs sur 4 — '
    'trois faux amis constatés : offre commerciale (Spirica), fenêtre de cumul YTD (Cardif), '
    'durée de contrat (Himalia). Renseignée par le contexte du run, jamais déduite du texte.';

-- 5 — L'ID de template natif est un pré-filtre, pas une signature ---------------------------
-- `TYPE_MODELE=66` chez Cardif vaut la même chose AVANT et APRÈS une refonte à laquelle une
-- seule ancre sur onze survit : il identifie une famille de document, pas un gabarit. Le
-- commentaire du DDL affirmait l'inverse (« signature parfaite, court-circuite le matching »).
COMMENT ON COLUMN gabarits.template_id_natif IS
    'Identifiant de template exposé par l''émetteur, quand il en expose un (Cardif : '
    'TYPE_MODELE=66). PRÉ-FILTRE de famille de document — il ne court-circuite PAS le '
    'matching en couches : vérifié identique de part et d''autre de la refonte Cardif 2025.';

COMMIT;

-- ============================================================================
-- Contrôles après migration
-- ============================================================================
-- \d gabarits                    -- valide_depuis NOT NULL, valide_jusqu_a nullable
-- SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
--   WHERE conrelid = 'ref.gabarits'::regclass ORDER BY conname;
--
-- Attendu : gabarit_version_unique UNIQUE (emetteur_code, gabarit, valide_depuis)
--           gabarit_fenetre_coherente CHECK (...)
--           et PLUS de gabarit_couple_unique.
--
-- ============================================================================
-- Défaire
-- ============================================================================
-- BEGIN;
-- ALTER TABLE ref.gabarits DROP CONSTRAINT IF EXISTS gabarit_version_unique;
-- ALTER TABLE ref.gabarits DROP CONSTRAINT IF EXISTS gabarit_fenetre_coherente;
-- ALTER TABLE ref.gabarits DROP COLUMN IF EXISTS valide_depuis;
-- ALTER TABLE ref.gabarits DROP COLUMN IF EXISTS valide_jusqu_a;
-- ALTER TABLE ref.gabarits ADD CONSTRAINT gabarit_couple_unique
--     UNIQUE (emetteur_code, gabarit, periodicite);
-- -- ⚠ le DROP NOT NULL sur periodicite n'est PAS réversible sans données : le remettre
-- --   échouerait s'il existe des lignes à periodicite NULL. Les renseigner d'abord.
-- COMMIT;
