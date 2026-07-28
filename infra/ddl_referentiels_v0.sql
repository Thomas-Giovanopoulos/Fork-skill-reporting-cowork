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
-- est irréconciliable. Cas de référence : Wealins FC051727 — poche FAS
-- Intesa → CA Indosuez ; poche FID CIC → Quintet, clôturée le 30/12/2025.
CREATE TABLE acteur_successions (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    predecesseur_code text NOT NULL REFERENCES acteurs(code) ON UPDATE CASCADE,
    successeur_code   text NOT NULL REFERENCES acteurs(code) ON UPDATE CASCADE,
    date_effet        date,                          -- NULL = date inconnue, à demander
    date_cloture      date,
    contexte          text,                          -- ex. 'Wealins FC051727 — poche FID'
    payload           jsonb NOT NULL DEFAULT '{}'::jsonb,
    provenance        provenance_t NOT NULL,
    confiance         confiance_t  NOT NULL,
    validated_by      text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT succession_non_reflexive CHECK (predecesseur_code <> successeur_code)
);

CREATE INDEX succ_pred_idx ON acteur_successions (predecesseur_code);
CREATE INDEX succ_succ_idx ON acteur_successions (successeur_code);
CREATE TRIGGER succ_touch BEFORE UPDATE ON acteur_successions
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();


-- ---------------------------------------------------------------------
-- §5 — Gabarits  [chantier N]
-- ---------------------------------------------------------------------
-- La clé est le COUPLE émetteur × gabarit × périodicité (D22). Motif : un même
-- émetteur peut publier plusieurs mises en page (Cardif mensuel ≠ trimestriel),
-- et la périodicité se discrimine par un TOKEN de libellé, pas par la date
-- d'arrêté (un trimestriel peut tomber au 31/12).
CREATE TABLE gabarits (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Clé étrangère vers l'acteur : les deux tables se chaînent, ne se
    -- substituent pas (D22).
    emetteur_code      text NOT NULL REFERENCES acteurs(code) ON UPDATE CASCADE,
    gabarit            text NOT NULL,                -- ex. 'releve_annuel_capi'
    periodicite        text NOT NULL,                -- annuel|trimestriel|mensuel|hebdomadaire|a_la_demande|inconnu

    -- ID de template natif quand l'émetteur en expose un : signature parfaite,
    -- court-circuite le matching en couches. Ex. Cardif : TYPE_MODELE 66.
    template_id_natif  text,

    -- La signature en trois couches (couche 1 metadata_pdf, couche 2
    -- ancres_texte, couche 3 marqueurs_structure) + token_periodicite.
    -- ⚠ Le nombre de pages est HORS matching : Dauphine 3→6 p., Wealins 15↔26 p.
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

    CONSTRAINT gabarit_couple_unique UNIQUE (emetteur_code, gabarit, periodicite)
);

CREATE INDEX gabarits_emetteur_idx  ON gabarits (emetteur_code);
CREATE INDEX gabarits_template_idx  ON gabarits (template_id_natif)
    WHERE template_id_natif IS NOT NULL;
CREATE INDEX gabarits_signature_gin ON gabarits USING gin (signature);
CREATE TRIGGER gabarits_touch BEFORE UPDATE ON gabarits
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();


-- ---------------------------------------------------------------------
-- §6 — ISIN  [chantier E]
-- ---------------------------------------------------------------------
-- Reprend exactement les colonnes de l'asset v0 (261 entrées) pour que la
-- promotion soit un simple COPY : isin,label,class_code,geo_code,sri,source,confidence.
CREATE TABLE isin (
    isin          char(12) PRIMARY KEY,
    label         text,
    class_code    text,                    -- 13 classes provisoires
    geo_code      text,                    -- 5 géographies provisoires ; NULL = non tagué (jamais de géo fausse)
    sri           smallint CHECK (sri IS NULL OR sri BETWEEN 1 AND 7),
    source        text,                    -- ex. 'interagyr_valide', 'gronier_categories'
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
    -- ex. gabarit : {"emetteur_code": "...", "gabarit": "...", "periodicite": "..."}
    cle                   jsonb NOT NULL,

    -- Le contenu proposé, mappé sur les colonnes de la table canonique à l'accept.
    proposition           jsonb NOT NULL,

    motif                 text,             -- pourquoi : drift détecté, ISIN inconnu, alias nouveau…
    run_id                text,             -- trace du run d'origine
    source_document       text,

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
