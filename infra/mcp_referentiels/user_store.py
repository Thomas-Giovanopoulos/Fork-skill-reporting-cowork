"""Registre des utilisateurs — source de vérité pour les permissions.

Mince adaptateur au-dessus de ``rhetores_authz``, identique à celui de
``mcp-o2s-server`` : même registre, mêmes comptes, mêmes rôles. Deux serveurs,
**un seul** registre — un CGP admin dans O2S est admin ici, et le retirer d'un
côté le retire de l'autre. C'est voulu : l'autonomie de déploiement du serveur
(D37) ne doit pas produire deux vérités sur qui est administrateur.

⚠️ PIÈGE DE DÉPLOIEMENT, à lire avant de remplir le ``.env``.

``make_authz_store()`` choisit son backend sur la présence de **``DATABASE_URL``**
(Postgres si présent, ``users.json`` sinon). Ce n'est **pas**
``REFERENTIELS_DATABASE_URL``. Les deux variables ne désignent pas la même base
et ne servent pas au même usage :

    DATABASE_URL               → registre utilisateurs (qui est admin)
    REFERENTIELS_DATABASE_URL  → référentiels du skill (acteurs, gabarits, ISIN)

Conséquence concrète : un serveur où l'on n'a défini que
``REFERENTIELS_DATABASE_URL`` sert les référentiels depuis Postgres et lit les
utilisateurs depuis ``users.json``. C'est une configuration **valide** — c'est
même celle de la boucle de dev — mais il faut alors que ``users.json`` (ou
``USERS_JSON``) soit présent, sinon tout appel authentifié tombe en 403
« Utilisateur non référencé » alors que le token est bon. Le symptôme ressemble
à un problème d'authentification ; c'est un fichier absent.

Ne PAS « corriger » cela en pointant ``DATABASE_URL`` sur ``rhetores_ref`` : la
séparation des deux bases est D33, et le registre utilisateurs n'a pas ses
tables dans le schéma ``ref``.

Variables d'environnement (lues par ``rhetores_authz``) :
    DATABASE_URL        Présence -> backend PostgreSQL (PgAuthzStore, D12).
    USERS_JSON          Contenu JSON brut du registre (prioritaire sur le fichier).
    USERS_FILE          Chemin du fichier JSON (défaut : users.json).
    USERS_CACHE_TTL     Durée du cache en secondes (défaut : 300).
"""

from rhetores_authz import User, make_authz_store

__all__ = ["User", "get_user", "reload", "store"]

# Une seule instance par processus — c'est elle que le middleware JWT utilise
# via get_user(), et c'est elle que les tools doivent réutiliser plutôt que
# d'en instancier une seconde (double lecture disque, ou connexion superflue).
_store = make_authz_store()


def get_user(oid: str) -> User | None:
    """Retourne l'utilisateur correspondant à l'OID, ou None si inconnu/inactif."""
    return _store.get_user(oid)


def reload() -> None:
    """Force le rechargement depuis le fichier (tests, rechargement à chaud).

    N'a d'effet qu'en mode JSON — no-op en mode Postgres, qui relit à chaque appel.
    """
    if hasattr(_store, "reload"):
        _store.reload()


def store():
    """Expose l'instance ``AuthzStore`` partagée du processus."""
    return _store
