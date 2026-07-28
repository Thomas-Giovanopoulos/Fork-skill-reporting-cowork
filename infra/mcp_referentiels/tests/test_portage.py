#!/usr/bin/env python3
"""Tests du portage vers le serveur dédié — exécutables SANS infra.

Ce qui rend ces tests possibles hors réseau : les deux correctifs du portage
portent sur de la logique **pure** (lecture de claims, choix d'une requête), pas
sur l'accès à Postgres. On peut donc les vérifier avec des bouchons, alors que
les quatre outils eux-mêmes exigent une base.

Ce qui est couvert :
  1. ``_identity()`` lit ``roles`` (liste) — le contrat réel de jwt_auth ;
  2. le repli sur le registre utilisateurs n'est plus emprunté quand les claims
     du middleware sont présents. C'est le cœur du correctif : le comportement
     observable est le même, seul le nombre d'accès au registre change, donc un
     test de valeur de retour ne l'aurait pas attrapé — on compte les appels ;
  3. ``ref_adjudications`` calcule sa répartition sur le périmètre de l'appelant.

Ce qui n'est PAS couvert et ne peut pas l'être ici : tout ce qui touche la base
(``_tx``, l'UPSERT canonique, l'atomicité de l'arbitrage). Cf. RUNBOOK §2.6.

Lancement :
    cd infra/mcp_referentiels && python3 tests/test_portage.py
"""
import sys
import types
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

# ─── Bouchons ────────────────────────────────────────────────────────────────
# `jwt_auth` importe rhetores_authz (absent d'un environnement nu) et
# `mcp.server.fastmcp` n'est pas nécessaire pour ces trois vérifications. On les
# remplace AVANT l'import du module testé. Aucun code de production n'est
# modifié pour les tests.

_claims: ContextVar[dict] = ContextVar("current_claims", default={})

faux_jwt = types.ModuleType("jwt_auth")
faux_jwt.current_claims = _claims
sys.modules["jwt_auth"] = faux_jwt

APPELS_REGISTRE = []


class FauxUtilisateur:
    def __init__(self, email, role):
        self.email, self.role = email, role


faux_store = types.ModuleType("user_store")


def _get_user(oid):
    APPELS_REGISTRE.append(oid)
    return FauxUtilisateur("registre@rhetores.com", "admin") if oid == "oid-admin" else None


faux_store.get_user = _get_user
sys.modules["user_store"] = faux_store

faux_mcp = types.ModuleType("mcp")
faux_serveur = types.ModuleType("mcp.server")
faux_fastmcp = types.ModuleType("mcp.server.fastmcp")
faux_fastmcp.FastMCP = object
sys.modules.update({"mcp": faux_mcp, "mcp.server": faux_serveur,
                    "mcp.server.fastmcp": faux_fastmcp})

from tools import referentiels as R  # noqa: E402

echecs = []


def verifie(intitule, obtenu, attendu):
    ok = obtenu == attendu
    print(f"  {'OK   ' if ok else 'ECHEC'} {intitule}")
    if not ok:
        print(f"        obtenu  : {obtenu!r}\n        attendu : {attendu!r}")
        echecs.append(intitule)


# ─── 1. Claims du middleware : roles au pluriel ──────────────────────────────
print("_identity — forme des claims produite par JWTAuthMiddleware")

APPELS_REGISTRE.clear()
_claims.set({"sub": "oid-1", "email": "cgp@rhetores.com", "roles": ["admin"]})
verifie("admin reconnu depuis roles=['admin']", R._identity(), ("cgp@rhetores.com", True))
verifie("aucun accès au registre (correctif)", APPELS_REGISTRE, [])

APPELS_REGISTRE.clear()
_claims.set({"sub": "oid-2", "email": "cgp@rhetores.com", "roles": ["conseiller"]})
verifie("non-admin reconnu", R._identity(), ("cgp@rhetores.com", False))
verifie("aucun accès au registre pour un non-admin", APPELS_REGISTRE, [])

# Régression du défaut d'origine : avec roles=['admin'], la version initiale
# lisait claims['role'] -> None, retombait sur get_user(sub) -> None (oid-1
# inconnu du faux registre) et concluait NON-admin. Un admin se voyait refuser
# l'arbitrage, ou bien le registre était interrogé à chaque appel.
APPELS_REGISTRE.clear()
_claims.set({"sub": "oid-inconnu", "email": "admin@rhetores.com", "roles": ["admin"]})
verifie("admin non dégradé par un registre muet", R._identity()[1], True)

# ─── 2. Replis conservés ─────────────────────────────────────────────────────
print("\n_identity — replis (claims d'une autre provenance)")

APPELS_REGISTRE.clear()
_claims.set({"sub": "oid-x", "email": "a@b.c", "role": "admin"})
verifie("tolérance au singulier", R._identity(), ("a@b.c", True))
verifie("singulier : pas d'accès au registre", APPELS_REGISTRE, [])

APPELS_REGISTRE.clear()
_claims.set({"sub": "oid-admin"})
verifie("repli registre quand aucun rôle en contexte",
        R._identity(), ("registre@rhetores.com", True))
verifie("repli : le registre EST interrogé", APPELS_REGISTRE, ["oid-admin"])

APPELS_REGISTRE.clear()
_claims.set({"sub": "oid-fantome"})
verifie("fail-safe : identité inconnue -> non-admin", R._identity(), ("", False))

APPELS_REGISTRE.clear()
_claims.set({})
verifie("claims vides -> non identifié, non-admin", R._identity(), ("", False))

# ─── 3. Répartition sur le périmètre de l'appelant ───────────────────────────
print("\nref_adjudications — la répartition suit le périmètre de la liste")

REQUETES = []


class FauxCurseur:
    def execute(self, sql, params=None):
        REQUETES.append((" ".join(sql.split()), params))

    def fetchall(self):
        return []


@contextmanager
def faux_tx(role):
    yield FauxCurseur()


R._tx = faux_tx


def collecter(claims):
    REQUETES.clear()
    _claims.set(claims)
    outils = {}

    class FauxMCP:
        def tool(self):
            def deco(fn):
                outils[fn.__name__] = fn
                return fn
            return deco

    R.register(FauxMCP())
    import asyncio
    asyncio.run(outils["ref_adjudications"]())
    return [q for q, _ in REQUETES], [p for _, p in REQUETES]


sql_admin, _ = collecter({"sub": "o", "email": "admin@r.com", "roles": ["admin"]})
verifie("admin : agrégat global, sans filtre",
        [("WHERE propose_par" in q) for q in sql_admin if "count(*)" in q], [False])

sql_cgp, params_cgp = collecter({"sub": "o", "email": "cgp@r.com", "roles": ["conseiller"]})
agregats = [(q, p) for q, p in zip(sql_cgp, params_cgp) if "count(*)" in q]
verifie("non-admin : agrégat filtré (correctif de fuite)",
        [("WHERE propose_par" in q) for q, _ in agregats], [True])
verifie("non-admin : filtré sur SON email", [p for _, p in agregats], [("cgp@r.com",)])

print(f"\n{'ECHEC' if echecs else 'OK'} — {len(echecs)} échec(s)")
sys.exit(1 if echecs else 0)
