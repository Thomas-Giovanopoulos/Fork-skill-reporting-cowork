-- ============================================================================
-- Migration 002 — D44 : aucun identifiant client dans le store des référentiels
-- ============================================================================
--   docker exec rhetores-dev-db psql -U rhetores -d rhetores_ref -v ON_ERROR_STOP=1 \
--       -f /tmp/migration_002_purge_identifiants_clients.sql
--
-- Rejouable : chaque étape est gardée par un test d'existence.
-- À jouer AVANT tout hébergement hors du poste (D43).
--
-- ---------------------------------------------------------------------------
-- POURQUOI — ce n'est pas une précaution de conformité, c'est une fuite active
-- ---------------------------------------------------------------------------
-- `ref_bundle` rend la base **en entier à chaque CGP** : c'est tout l'objet de D36, un gabarit
-- validé par l'un doit être visible du suivant. Conséquence rarement énoncée : **tout
-- identifiant client qui entre dans cette base est visible de tous les CGP.**
--
-- Le défaut était déjà là, en local, indépendamment de tout hébergement. Les deux successions
-- du seed portaient :
--
--     contexte = 'Wealins FC051727 — poche FAS'
--     contexte = 'Wealins FC051727 — poche FID'
--
-- soit un **numéro de contrat réel**. N'importe quel CGP appelant le bundle apprenait donc qu'un
-- client détient ce contrat, avec une poche ex-Intesa. Ce n'est pas un risque théorique de
-- prestataire d'hébergement : c'est une divulgation entre confrères, et elle était opérante.
--
-- La distinction qui tranche : une succession est un **fait de marché** — « la poche ex-Intesa a
-- été reprise par CA Indosuez ». Le numéro de contrat n'est pas le fait, c'est **l'endroit où on
-- l'a observé**. Sa place est le dossier de run du client, jamais un référentiel partagé.
--
-- ---------------------------------------------------------------------------
-- CE QUI RESTE, ET POURQUOI
-- ---------------------------------------------------------------------------
-- Les e-mails de CGP (`propose_par`, `arbitre_par`, `validated_by`) sont **conservés**. Ce sont
-- des données professionnelles, et la responsabilité nominative est la contrepartie exacte du
-- privilège d'arbitrage (D34) : « qui a canonisé quoi » doit rester lisible, sinon la séparation
-- proposer / canoniser n'a plus de témoin. Les retirer affaiblirait le dispositif sans protéger
-- personne d'utile.
-- ============================================================================

SET search_path TO ref, public;

BEGIN;

-- 1 — `adjudications.source_document` : du nom de fichier à l'empreinte -----------------------
-- Le nom de fichier porte le client en clair (« Relevé Himalia Capi HANAMI.pdf »). Ce qu'un
-- arbitre a réellement besoin de savoir, c'est de QUEL TYPE de document vient la proposition et
-- à quelle date d'arrêté — pas de qui. Le remplacement est donc à la fois moins révélateur et
-- **plus utile** : l'empreinte du CONTENU permet en plus de reconnaître deux propositions issues
-- du même document, ce qu'un nom de fichier ne garantit jamais.
ALTER TABLE adjudications
    ADD COLUMN IF NOT EXISTS source_empreinte text,   -- sha256 du CONTENU du document
    ADD COLUMN IF NOT EXISTS source_gabarit   text,   -- gabarit apparié, ex. 'releve_annuel_capi_lux'
    ADD COLUMN IF NOT EXISTS source_arrete    date;   -- date d'arrêté, non identifiante

COMMENT ON COLUMN adjudications.source_empreinte IS
    'sha256 du CONTENU du document source. Remplace le nom de fichier, qui portait le nom du '
    'client en clair (D44). Permet de reconnaître deux propositions issues du même document — '
    'ce qu''un nom de fichier ne garantit pas.';
COMMENT ON COLUMN adjudications.source_gabarit IS
    'Gabarit apparié au document source. C''est la traçabilité utile à l''arbitre : de quel TYPE '
    'de relevé vient la proposition.';
COMMENT ON COLUMN adjudications.source_arrete IS
    'Date d''arrêté du document source. Non identifiante, et nécessaire pour choisir la version '
    'de gabarit applicable (D42).';

-- Report de l'existant, s'il y en a. Au 2026-07-29 les deux seules lignes ont
-- `source_document IS NULL` : le report est donc vide, et c'est le bon moment pour migrer.
UPDATE adjudications
   SET source_gabarit = COALESCE(source_gabarit, '(inconnu — repris de source_document)')
 WHERE source_document IS NOT NULL
   AND source_gabarit IS NULL;

-- La colonne fautive part. On ne la garde pas « au cas où » : une colonne de PII conservée est
-- une PII conservée, et le motif de cette migration est précisément qu'elle ne doit plus exister.
ALTER TABLE adjudications DROP COLUMN IF EXISTS source_document;

-- 2 — `acteur_successions.contexte` : le fait, pas l'instance ---------------------------------
-- Réécriture des deux lignes du seed. Le numéro de contrat disparaît ; ce qui reste décrit la
-- succession elle-même, qui est vraie pour tous les clients concernés.
UPDATE acteur_successions
   SET contexte = 'reprise de la poche FAS ex-Intesa chez un assureur luxembourgeois'
 WHERE predecesseur_code = 'intesa_sanpaolo' AND successeur_code = 'ca_indosuez';

UPDATE acteur_successions
   SET contexte = 'reprise de la poche FID ex-CIC chez un assureur luxembourgeois'
 WHERE predecesseur_code = 'cic' AND successeur_code = 'quintet';

-- Garde-fou : un `contexte` ne doit plus ressembler à une référence de contrat. Le motif visé
-- est une suite de deux lettres et cinq à huit chiffres (FC051727, FC055211, K00149YU…), qui est
-- la forme des références rencontrées chez Wealins et Quintet. Volontairement étroit : une
-- contrainte trop large rejetterait des descriptions légitimes et serait désactivée au premier
-- faux positif — ce qui est pire qu'aucune contrainte.
ALTER TABLE acteur_successions DROP CONSTRAINT IF EXISTS succession_contexte_sans_reference;
ALTER TABLE acteur_successions ADD CONSTRAINT succession_contexte_sans_reference
    CHECK (contexte IS NULL OR contexte !~ '[A-Z]{2}[0-9]{5,8}');

COMMENT ON COLUMN acteur_successions.contexte IS
    'Description du FAIT DE MARCHÉ, jamais de l''instance où on l''a observé (D44). Interdit : '
    'numéro de contrat, nom de client, identifiant de poche. Le store est rendu en entier à '
    'chaque CGP par ref_bundle : ce qui entre ici est visible de tous.';

COMMIT;

-- ============================================================================
-- Contrôles après migration
-- ============================================================================
-- \d adjudications        -- source_document absente ; trois colonnes source_* présentes
-- SELECT contexte FROM ref.acteur_successions;   -- aucun numéro de contrat
--
-- Le garde-fou se vérifie en tentant de le violer — un contrôle qu'on n'a pas vu échouer ne
-- prouve rien :
--   INSERT INTO ref.acteur_successions (predecesseur_code, successeur_code, contexte,
--                                       provenance, confiance)
--   VALUES ('cic', 'quintet', 'poche FID du contrat FC051727', 'seed', 'low');
--   -- attendu : ERROR ... violates check constraint "succession_contexte_sans_reference"
--
-- ============================================================================
-- Défaire
-- ============================================================================
-- ⚠ Le retour en arrière ne restaure PAS les valeurs d'origine : elles contenaient les
--   identifiants clients que cette migration existe pour supprimer. C'est voulu.
-- BEGIN;
-- ALTER TABLE ref.acteur_successions DROP CONSTRAINT IF EXISTS succession_contexte_sans_reference;
-- ALTER TABLE ref.adjudications ADD COLUMN IF NOT EXISTS source_document text;
-- ALTER TABLE ref.adjudications DROP COLUMN IF EXISTS source_empreinte;
-- ALTER TABLE ref.adjudications DROP COLUMN IF EXISTS source_gabarit;
-- ALTER TABLE ref.adjudications DROP COLUMN IF EXISTS source_arrete;
-- COMMIT;
