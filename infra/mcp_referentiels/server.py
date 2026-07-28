"""Serveur MCP des référentiels du skill de reporting — point d'entrée.

Serveur **autonome** (D37). Décision de Thomas : on ne greffe pas un module
``tools/`` sur ``mcp-o2s-server``. Motifs : cycle de vie et déploiement
indépendants, aucun risque de régression sur O2S, et au moment de la
convergence datahub on débranche un serveur entier plutôt que de démêler un
module.

Le framework est calqué sur ``mcp-o2s-server/server.py`` — Starlette + FastMCP
en streamable HTTP, middleware JWT, sonde ``/health`` dispensée d'auth.

Variables d'environnement — cf. ``.env.example`` :
    REFERENTIELS_DATABASE_URL  DSN de la base des référentiels. DÉLIBÉRÉMENT
                               distinct de ``DATABASE_URL`` : c'est lui qui
                               garantit la séparation d'avec la projection du
                               datahub (D33).
    JWT_SECRET                 recette (HS256), ou
    AZURE_TENANT_ID + AZURE_AUDIENCE   production (RS256)
    ALLOWED_ORIGINS            défaut : https://claude.ai
    PORT                       défaut : 8001 (O2S occupe 8000)

Lancement :
    uvicorn server:app --host 0.0.0.0 --port 8001

Le serveur DÉMARRE même sans ``REFERENTIELS_DATABASE_URL`` : l'import de
psycopg est différé et le DSN n'est résolu qu'à l'appel d'un outil. On préfère
un serveur qui répond ``/health`` et échoue avec un message clair sur
``ref_bundle`` à un serveur qui refuse de démarrer — le diagnostic est plus
rapide. Un avertissement est journalisé au démarrage.
"""

import contextlib
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from jwt_auth import JWTAuthMiddleware
from logging_config import setup_logging

setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"))

from tools import referentiels

log = logging.getLogger("mcp.ref")

_DSN_ENV = "REFERENTIELS_DATABASE_URL"

if not os.environ.get(_DSN_ENV):
    log.warning(
        "referentiels_non_configures",
        extra={"variable": _DSN_ENV,
               "consequence": "les outils ref_* échoueront avec un message explicite"},
    )
if os.environ.get(_DSN_ENV) and os.environ.get(_DSN_ENV) == os.environ.get("DATABASE_URL"):
    # Garde-fou D33. Les deux bases doivent être distinctes : la projection du
    # datahub ne doit pas héberger les référentiels du skill. Une égalité ici
    # est presque sûrement un copier-coller de DSN.
    log.error(
        "dsn_confondus",
        extra={"variable": _DSN_ENV,
               "consequence": "REFERENTIELS_DATABASE_URL == DATABASE_URL — violation de D33"},
    )

mcp = FastMCP(
    "Claude.ia referentiels-Rhetores",
    stateless_http=True,
    json_response=True,
    host="0.0.0.0",
)

referentiels.register(mcp)


@contextlib.asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield


async def health(request):
    """Sonde de santé — sans dépendance, dispensée de JWT.

    Expose un booléen de configuration, jamais le DSN : l'endpoint n'est pas
    authentifié (cf. ``JWTAuthMiddleware._BYPASS_PATHS``).
    """
    return JSONResponse({
        "status": "ok",
        "service": "mcp-referentiels",
        "referentiels_configures": bool(os.environ.get(_DSN_ENV)),
    })


app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Mount("/", app=mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)

app.add_middleware(JWTAuthMiddleware)

if __name__ == "__main__":
    mcp.run()
