-- =====================================================================
-- Référentiels du skill de reporting — DDL v0
-- Postgres 16 (parité Azure Flexible Server, cf. docker-compose fo-data-store)
--
-- BASE SÉPARÉE de la projection du datahub (D33) : on s'inspire de ses
-- conventions (colonnes promues + payload JSONB), on ne touche pas à ses tables.
-- Cette base est la STAGING DU FORK côté données ; son contenu sera replié
-- dans le datahub au retour vers Code (M7).
--
-- Trois tables canoniques + une file d'adjudication :
--   acteurs             qui est cette entité, quel rôle          [chantier K]
--   acteur_successions  X devenu Y, à telle date                [K5]
--   gabarits            de quel template ce document relève      [chantier N]
--   isin                classe / géo / SRI par ISIN              [chantier E]
--   adjudications       la file des propositions à arbitrer      [D34, N6]
--
-- La séparation « proposer ≠ canoniser » (D34) est portée par des RÔLES
-- POSTGRES, pas par une convention applicative : voir §6.
--
-- PARITÉ AVEC LES MIGRATIONS — ce DDL sert aux installations NEUVES, les
-- migrations aux bases déjà créées ; les deux doivent aboutir au MÊME schéma.
-- Sont donc intégrées ici :
--   migration_001  fenêtre de validité des gabarits (D42) ;
--   migration_002  aucun identifiant client dans le store (D44) — trois
--                  colonnes `source_*` sur `adjudications` en remplacement de
--                  `source_document`, et le CHECK
--                  `succession_contexte_sans_reference` sur `contexte`.
-- Toute modification ici doit être répercutée là-bas, et réciproquement.
--
-- Ordre d'exécution :
--   1. §0 hors de la base cible (connecté à `postgres`)
--   2. §1 à §7 connecté à la base cible
-- =====================================================================


-- ---------------------------------------------------------------------
-- §0 — Création de la base (à exécuter HORS de la base cible)
-- ---------------------------------------------------------------------
-- CREATE DATABASE rhetores_ref
--   WITH ENCODING 'UTF8' LC_COLLATE 'fr_FR.UTF-8' LC_CTYPE 'fr_FR.UTF-8'
--   TEMPLATE template0;
--
-- Puis : \c rhetores_ref


-- ---------------------------------------------------------------------
-- §1 — Conventions communes
-- ---------------------------------------------------------------------
-- gen_random_uuid() est natif depuis PG13 : aucune extension requise.

CREATE SCHEMA IF NOT EXISTS ref;
SET search_path TO ref, public;

-- Provenance d'une entrée : d'où elle vient, et donc quelle confiance lui prêter.
CREATE TYPE provenance_t AS ENUM ('seed', 'auto_derive', 'valide_admin');

-- Confiance : reprend l'échelle du contrat de diff (high/medium/low).
CREATE TYPE confiance_t AS ENUM ('high', 'medium', 'low');

-- Rôle d'un acteur. « plateforme » = grossiste (Nortia), qui n'est PAS un assureur.
CREATE TYPE role_acteur_t AS ENUM ('assureur', 'depositaire', 'gerant', 'plateforme');

-- Cible et statut d'une demande d'adjudication.
CREATE TYPE cible_t AS ENUM ('acteur', 'succession', 'gabarit', 'isin');
CREATE TYPE statut_adj_t AS ENUM ('en_attente', 'accepte', 'rejete');

-- Nature de la proposition — les trois natures de N6, plus les cas des autres tables.
-- Elles n'appellent pas le même arbitrage : c'est le point de N6.
CREATE TYPE nature_adj_t AS ENUM (
    'nouvel_emetteur',        -- N6 : émetteur inconnu, donc gabarit inconnu
    'nouveau_gabarit',        -- N6 : émetteur connu, gabarit nouveau
    'variante_periodicite',   -- N6 : émetteur + gabarit connus, périodicité nouvelle
    'nouvel_acteur',
    'nouvelle_succession',
    'nouvel_isin',
    'mise_a_jour'             -- entrée existante à amender (drift, alias, géo…)
);

-- Horodatage de modification, posé par trigger (jamais par l'applicatif).
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ---------------------------------------------------------------------
-- §2 — Méta : version de schéma
-- ---------------------------------------------------------------------
-- Le suffixe `-skill` est délibéré (D19/M4) : cette forme est celle du fork,
-- pas celle du store béni. Ne jamais revendiquer un numéro officiel.
CREATE TABLE ref_meta (
    cle     text PRIMARY KEY,
    valeur  text NOT NULL,
    note    text
);

INSERT INTO ref_meta (cle, valeur, note) VALUES
    ('schema_version', '0.1-skill',
     'Forme du fork. Repliée dans le datahub au retour vers Code (M7).'),
    ('registre_ecarts', 'voir le registre des écarts du fork',
     'Aucune clé posée ici sans son entrée au registre (D21).');


-- ---------------------------------------------------------------------
-- §3 — Acteurs  [chantier K]
-- ---------------------------------------------------------------------
-- Émetteur ≠ distributeur ≠ nom de fichier (D24). Un acteur porte un code
-- canonique stable ; ses libellés verbatim vivent dans `alias`.
CREATE TABLE acteurs (
    code              text PRIMARY KEY,            -- ex. 'spirica', 'de_pury_pictet'
    nom               text        NOT NULL,         -- raison sociale de référence
    role              role_acteur_t NOT NULL,
    domiciliation     char(2),                      -- 'FR','LU','CH'… NULL = non déterminée

    -- Lève l'homonymie « NC » (D26/T5) : NC = « non communicable », convention
    -- réglementaire des contrats FR sans dépositaire tiers (triangle de sécurité),
    -- à ne PAS confondre avec « non renseigné ».
    est_depositaire_tiers boolean,

    -- Libellés verbatim tels qu'ils apparaissent dans les PDF. `text[]` plutôt
    -- que jsonb : containment indexable par GIN. Ex. pour de Pury Pictet, la
    -- convention d'affichage est « De Pury Pictet », jamais « PPT ».
    alias             text[]      NOT NULL DEFAULT '{}',

    -- Couples admissibles (assureur × dépositaire), notes, libellé d'affichage…
    payload           jsonb       NOT NULL DEFAULT '{}'::jsonb,

    provenance        provenance_t NOT NULL,
    confiance         confiance_t  NOT NULL,
    version           integer      NOT NULL DEFAULT 1,
    validated_by      text,                          -- email de session
    created_at        timestamptz  NOT NULL DEFAULT now(),
    updated_at        timestamptz  NOT NULL DEFAULT now()
);

CREATE INDEX acteurs_alias_gin ON acteurs USING gin (alias);
CREATE INDEX acteurs_role_idx  ON acteurs (role);
CREATE TRIGGER acteurs_touch BEFORE UPDATE ON acteurs
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();


-- ---------------------------------------------------------------------
-- §4 — Successions d'acteurs  [K5]
-- ---------------------------------------------------------------------
-- Sans succession datée, un relevé antérieur à un changement de dépositaire
-- est irréconciliable. Cas de référence, chez un assureur luxembourgeois :
-- poche FAS Intesa → CA Indosuez ; poche FID CIC → Quintet, clôturée le
-- 30/12/2025. Le CONTRAT où on l'a observé n'a pas sa place ici (D44) : c'est
-- la succession qui est un fait de marché, pas l'instance qui l'a révélée.
CREATE TABLE acteur_successions (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    predecesseur_code text NOT NULL REFERENCES acteurs(code) ON UPDATE CASCADE,
    successeur_code   text NOT NULL REFERENCES acteurs(code) ON UPDATE CASCADE,
    date_effet        date,                          -- NULL = date inconnue, à demander
    date_cloture      date,
    contexte          text,                          -- le FAIT, ex. 'reprise de la poche FID ex-CIC'
    payload           jsonb NOT NULL DEFAULT '{}'::jsonb,
    provenance        provenance_t NOT NULL,
    confiance         confiance_t  NOT NULL,
    validated_by      text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT succession_non_reflexive CHECK (predecesseur_code <> successeur_code),

    -- D44, repris de migration_002. Un `contexte` ne doit pas ressembler à une référence
    -- de contrat : deux lettres suivies de cinq à huit chiffres, forme des références
    -- rencontrées chez Wealins et Quintet. Volontairement ÉTROIT : une contrainte trop
    -- large rejetterait des descriptions légitimes et serait désactivée au premier faux
    -- positif — ce qui est pire qu'aucune contrainte.
    CONSTRAINT succession_contexte_sans_reference
        CHECK (contexte IS NULL OR contexte !~ '[A-Z]{2}[0-9]{5,8}')
);

COMMENT ON COLUMN acteur_successions.contexte IS
    'Description du FAIT DE MARCHÉ, jamais de l''instance où on l''a observé (D44). Interdit : '
    'numéro de contrat, nom de client, identifiant de poche. Le store est rendu en entier à '
    'chaque CGP par ref_bundle : ce qui entre ici est visible de tous.';

CREATE INDEX succ_pred_idx ON acteur_successions (predecesseur_code);
CREATE INDEX succ_succ_idx ON acteur_successions (successeur_code);
CREATE TRIGGER succ_touch BEFORE UPDATE ON acteur_successions
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();


-- ---------------------------------------------------------------------
-- §5 — Gabarits  [chantier N]
-- ---------------------------------------------------------------------
-- La clé est le TRIPLET émetteur × gabarit × valide_depuis (D42). Ce DDL et
-- infra/migration_001_d42_fenetre_validite.sql doivent aboutir au MÊME schéma :
-- le DDL sert aux installations neuves, la migration aux bases déjà créées.
-- Toute modification ici doit être répercutée là-bas, et réciproquement.
--
-- Deux motifs, tirés du corpus du 2026-07-29 :
--  (a) la périodicité n'est PAS LISIBLE dans le document chez trois émetteurs sur
--      quatre, et ses tokens candidats sont des faux amis — elle ne peut pas
--      porter une clé d'appariement, elle devient informative ;
--  (b) un émetteur change de maquette : Cardif a produit deux gabarits en douze
--      mois, une seule ancre sur onze survit de l'un à l'autre. Sans fenêtre de
--      validité, le nouveau format ÉCRASE l'ancien et les relevés archivés
--      deviennent inparsables — or un run réel lit des relevés jusqu'à 2022.
--      À l'inverse Himalia n'a pas bougé en treize mois : la fenêtre est une
--      CAPACITÉ, pas une règle.
CREATE TABLE gabarits (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Clé étrangère vers l'acteur : les deux tables se chaînent, ne se
    -- substituent pas (D22).
    emetteur_code      text NOT NULL REFERENCES acteurs(code) ON UPDATE CASCADE,
    gabarit            text NOT NULL,                -- ex. 'releve_annuel_capi'

    -- Fenêtre de validité (D42). '0001-01-01' = « depuis toujours ».
    -- ⚠ `valide_depuis` est NOT NULL À DESSEIN, et ce n'est pas du style : en SQL
    --   deux NULL sont DISTINCTS dans une contrainte d'unicité, donc deux profils
    --   (cardif, x, NULL) passeraient tous les deux et l'unicité ne protégerait
    --   plus rien. Pire, une cible d'ON CONFLICT contenant un NULL ne matche
    --   jamais : chaque adjudication acceptée par `ref_arbitrer` insérerait un
    --   doublon au lieu de mettre à jour, silencieusement. On préfère cette
    --   convention de date à `UNIQUE NULLS NOT DISTINCT` (PostgreSQL 15+) :
    --   elle ne dépend d'aucune version et se lit dans les données.
    valide_depuis      date NOT NULL DEFAULT '0001-01-01',
    valide_jusqu_a     date,                         -- NULL = toujours en cours

    -- INFORMATIVE, hors matching (D42) : donc nullable.
    periodicite        text,                         -- annuel|trimestriel|mensuel|hebdomadaire|a_la_demande|inconnu

    -- ID de template natif quand l'émetteur en expose un. PRÉ-FILTRE de famille de
    -- document, il ne court-circuite PAS le matching. Ex. Cardif : TYPE_MODELE 66.
    template_id_natif  text,

    -- La signature : `couche1` (métadonnées PDF) est un PRÉ-FILTRE D'ÉMETTEUR qui
    -- ne peut que restreindre ; `sections_requises` est une barrière (toutes
    -- présentes ou rejet), `sections_optionnelles` n'ajoute que de la confiance,
    -- `discriminants` pèse lourd. `_token_periodicite_refute` et
    -- `_marqueurs_structure_observes` sont de la DOCUMENTATION, non consommée.
    -- ⚠ Le nombre de pages est HORS matching : Dauphine 3→6 p., Wealins 10↔26 p.
    --   pour le même gabarit. `n_pages_indicatif` est informatif seulement.
    signature          jsonb NOT NULL,
    n_pages_indicatif  text,

    -- Pièges de parsing et ancrages, migrés hors du prompt (N3).
    extraction_hints   jsonb NOT NULL DEFAULT '{}'::jsonb,

    -- Qui publie quoi : perf par ligne oui/non/par_poche/derivable, et sa forme.
    -- Évite de laisser un perf_pct vide par défaut (B9).
    champs_publies     jsonb NOT NULL DEFAULT '{}'::jsonb,

    -- Checksum interne du gabarit : Σ lignes = tel total, Σ % = 100…
    -- Auto-valide l'extraction sans humain (D25).
    invariant_controle text,

    -- Émetteur non lisible en texte (logo image seul : Nortia, Himalia) :
    -- nommé par un humain une fois au seed, jamais deviné au runtime (D24/N7).
    emetteur_lisible   boolean NOT NULL DEFAULT true,

    provenance         provenance_t NOT NULL,
    confiance          confiance_t  NOT NULL,
    version            integer      NOT NULL DEFAULT 1,
    validated_by       text,
    created_at         timestamptz  NOT NULL DEFAULT now(),
    updated_at         timestamptz  NOT NULL DEFAULT now(),

    -- Plusieurs profils peuvent partager (emetteur_code, gabarit) et se
    -- distinguer par leur début de validité : c'est le cas Cardif v1 / v2.
    CONSTRAINT gabarit_version_unique UNIQUE (emetteur_code, gabarit, valide_depuis),
    CONSTRAINT gabarit_fenetre_coherente
        CHECK (valide_jusqu_a IS NULL OR valide_jusqu_a >= valide_depuis)
);

COMMENT ON COLUMN gabarits.valide_depuis IS
    'Début de validité du gabarit. ''0001-01-01'' = depuis toujours. NOT NULL à dessein : '
    'un NULL casserait l''unicité (deux NULL sont distincts) et ferait insérer des doublons '
    'par l''ON CONFLICT de ref_arbitrer. Cf. migration_001.';
COMMENT ON COLUMN gabarits.valide_jusqu_a IS
    'Fin de validité, NULL = toujours en cours. Sert à CHOISIR entre versions, jamais à '
    'retirer un profil : un ancien gabarit doit rester lisible pour parser les archives '
    '(un run réel du corpus remonte à 2022). Limite L5 de l''étude de corpus.';
COMMENT ON COLUMN gabarits.periodicite IS
    'INFORMATIVE, hors matching (D42). Non lisible dans le document chez 3 émetteurs sur 4 — '
    'trois faux amis constatés : offre commerciale (Spirica), fenêtre de cumul YTD (Cardif), '
    'durée de contrat (Himalia). Renseignée par le contexte du run, jamais déduite du texte.';
COMMENT ON COLUMN gabarits.template_id_natif IS
    'Identifiant de template exposé par l''émetteur, quand il en expose un (Cardif : '
    'TYPE_MODELE=66). PRÉ-FILTRE de famille de document — il ne court-circuite PAS le '
    'matching en couches : vérifié identique de part et d''autre de la refonte Cardif 2025.';

CREATE INDEX gabarits_emetteur_idx  ON gabarits (emetteur_code);
CREATE INDEX gabarits_template_idx  ON gabarits (template_id_natif)
    WHERE template_id_natif IS NOT NULL;
CREATE INDEX gabarits_signature_gin ON gabarits USING gin (signature);
CREATE TRIGGER gabarits_touch BEFORE UPDATE ON gabarits
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();


-- ---------------------------------------------------------------------
-- §6 — ISIN  [chantier E]
-- ---------------------------------------------------------------------
-- Reprend exactement les colonnes de l'asset v0 (261 entrées) :
-- isin,label,class_code,geo_code,sri,source,confidence.
-- ATTENTION (D44) : ce n'est PLUS un simple COPY depuis le CSV. La colonne `source` de
-- l'asset nomme des CLIENTS (un nom de client suivi d'un suffixe) ; elle est
-- dé-identifiée à l'assemblage par seed/construire_bundle.py (SOURCE_ISIN_DEIDENTIFIEE).
-- Charger par seed/seed.sql, jamais par \copy sur le CSV brut.
CREATE TABLE isin (
    isin          char(12) PRIMARY KEY,
    label         text,
    class_code    text,                    -- 13 classes provisoires
    geo_code      text,                    -- 5 géographies provisoires ; NULL = non tagué (jamais de géo fausse)
    sri           smallint CHECK (sri IS NULL OR sri BETWEEN 1 AND 7),
    source        text,                    -- TYPE de source, jamais un client (D44) :
                                           -- ex. 'reporting_mandat_valide', 'run_reel_T2'
    provenance    provenance_t NOT NULL,
    confiance     confiance_t  NOT NULL,
    version       integer      NOT NULL DEFAULT 1,
    validated_by  text,
    created_at    timestamptz  NOT NULL DEFAULT now(),
    updated_at    timestamptz  NOT NULL DEFAULT now()
);

CREATE INDEX isin_class_idx ON isin (class_code);
CREATE INDEX isin_geo_null_idx ON isin (isin) WHERE geo_code IS NULL;  -- reste à compléter (E6)
CREATE TRIGGER isin_touch BEFORE UPDATE ON isin
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();


-- ---------------------------------------------------------------------
-- §7 — File d'adjudication  [D34, N6]
-- ---------------------------------------------------------------------
-- Une ligne par proposition. Append-only pour les non-admin : un run PROPOSE,
-- il ne canonise jamais. L'arbitrage est un UPDATE réservé à l'admin (§8).
CREATE TABLE adjudications (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cible                 cible_t      NOT NULL,
    nature                nature_adj_t NOT NULL,

    -- Identifiant proposé, forme dépendante de la cible.
    -- ex. gabarit : {"emetteur_code": "...", "gabarit": "...", "valide_depuis": "..."}
    -- (la clé suit gabarit_version_unique : la périodicité n'en fait plus partie, D42)
    cle                   jsonb NOT NULL,

    -- Le contenu proposé, mappé sur les colonnes de la table canonique à l'accept.
    proposition           jsonb NOT NULL,

    motif                 text,             -- pourquoi : drift détecté, ISIN inconnu, alias nouveau…
    run_id                text,             -- trace du run d'origine

    -- D44, repris de migration_002 : PAS de `source_document`. Un nom de fichier porte le
    -- client en clair (« Relevé … <NOM DU CLIENT>.pdf ») et ce store est rendu EN ENTIER à
    -- chaque CGP par ref_bundle (D36) : la colonne était une divulgation entre confrères.
    -- Le remplacement est à la fois moins révélateur et PLUS UTILE — ce qu'un arbitre a
    -- besoin de savoir est de quel TYPE de document vient la proposition et à quelle date
    -- d'arrêté, pas de qui ; et l'empreinte du CONTENU reconnaît deux propositions issues
    -- du même document, ce qu'un nom de fichier ne garantit jamais.
    source_empreinte      text,             -- sha256 du CONTENU du document
    source_gabarit        text,             -- gabarit apparié, ex. 'releve_annuel_capi_lux'
    source_arrete         date,             -- date d'arrêté, non identifiante

    propose_par           text NOT NULL,    -- email de session du proposant
    propose_le            timestamptz NOT NULL DEFAULT now(),

    statut                statut_adj_t NOT NULL DEFAULT 'en_attente',
    arbitre_par           text,
    arbitre_le            timestamptz,
    commentaire_arbitrage text,

    CONSTRAINT arbitrage_coherent CHECK (
        (statut = 'en_attente' AND arbitre_par IS NULL AND arbitre_le IS NULL)
        OR (statut <> 'en_attente' AND arbitre_par IS NOT NULL AND arbitre_le IS NOT NULL)
    )
);

CREATE INDEX adj_statut_idx  ON adjudications (statut, propose_le DESC);
CREATE INDEX adj_proposant_idx ON adjudications (propose_par);
CREATE INDEX adj_cible_idx   ON adjudications (cible, nature);

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

-- Les e-mails de CGP (`propose_par`, `arbitre_par`, `validated_by`) sont CONSERVÉS : ce sont
-- des données professionnelles, et la responsabilité nominative est la contrepartie exacte du
-- privilège d'arbitrage (D34). Les retirer affaiblirait le dispositif sans protéger personne.


-- ---------------------------------------------------------------------
-- §8 — Rôles : « proposer ≠ canoniser », appliqué par la base
-- ---------------------------------------------------------------------
-- D34 exigeait que la séparation soit une PERMISSION, pas une convention.
-- Deux rôles de groupe, et un rôle de connexion NOINHERIT qui n'a par défaut
-- AUCUN des deux : le module MCP fait `SET LOCAL ROLE` par transaction selon
-- les claims. Un bug applicatif ne peut donc pas canoniser à la place d'un CGP.

CREATE ROLE ref_app   NOLOGIN;   -- tout run authentifié : lit le canonique, propose
CREATE ROLE ref_admin NOLOGIN;   -- admin seul : écrit le canonique, arbitre

-- Lecture du canonique pour les deux rôles.
GRANT USAGE ON SCHEMA ref TO ref_app, ref_admin;
GRANT SELECT ON acteurs, acteur_successions, gabarits, isin, ref_meta
    TO ref_app, ref_admin;

-- ref_app : peut déposer une proposition et relire la file. Rien de plus.
GRANT SELECT, INSERT ON adjudications TO ref_app;

-- ref_admin : écrit le canonique et arbitre.
GRANT SELECT, INSERT, UPDATE, DELETE ON acteurs, acteur_successions, gabarits, isin
    TO ref_admin;
GRANT SELECT, INSERT, UPDATE ON adjudications TO ref_admin;
GRANT UPDATE ON ref_meta TO ref_admin;

-- Rôle de connexion du serveur MCP. NOINHERIT est le point clé : il est membre
-- des deux groupes mais n'en exerce aucun sans `SET ROLE` explicite.
-- Le mot de passe est injecté par variable d'environnement, jamais ici.
-- CREATE ROLE ref_mcp LOGIN NOINHERIT PASSWORD :'mdp';
-- GRANT ref_app, ref_admin TO ref_mcp;

-- Personne n'écrit le canonique par accident : on retire le défaut public.
REVOKE ALL ON ALL TABLES IN SCHEMA ref FROM PUBLIC;


-- ---------------------------------------------------------------------
-- §9 — Vérifications de bon sens
-- ---------------------------------------------------------------------
-- Rejouable : ce script se détruit proprement par
--   DROP SCHEMA ref CASCADE;
--   DROP ROLE ref_app, ref_admin;   -- (et ref_mcp le cas échéant)
--
-- Contrôle post-installation attendu :
--   SELECT valeur FROM ref_meta WHERE cle = 'schema_version';  -- '0.1-skill'
--   SELECT count(*) FROM acteurs;                              -- 0 avant le seed
