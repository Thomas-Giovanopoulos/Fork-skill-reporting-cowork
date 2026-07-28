"""Validation JWT et middleware Starlette — serveur des référentiels.

Reprise du middleware de ``mcp-o2s-server/jwt_auth.py``, **sans réécrire la
validation du token** : celle-ci reste déléguée à ``rhetores_authz.validate_token``,
paquet partagé avec ``fo-data-store/validation_app`` et ``mcp-o2s-server``.

Pourquoi importer plutôt que copier — le point important de ce fichier. Le fix
S11 (en HS256 comme en RS256, ``aud`` **et** ``iss`` sont vérifiés) vit dans
``rhetores_authz``. En recopier le code ici créerait une **seconde**
implémentation de validation de token, condamnée à diverger : le jour où un
défaut de validation est corrigé dans le paquet partagé, ce serveur resterait
vulnérable sans que rien ne le signale. Un serveur MCP autonome (D37) ne veut
pas dire une pile d'authentification autonome.

Deux modes, résolus par ``rhetores_authz`` selon l'environnement :
  - AZURE_TENANT_ID présent → RS256 via JWKS Azure Entra (production)
  - JWT_SECRET présent      → HS256 avec secret partagé (recette interne)

Ce module ne gère que ce qui est spécifique au MCP :
  - résolution de l'utilisateur via ``user_store`` (403 si inconnu/inactif) et
    reconstruction du périmètre dans ``current_claims`` **depuis le store**, pas
    depuis les claims bruts — un éventuel rôle porté par le JWT est ignoré ;
  - bypass JWT pour ``/health`` ;
  - contrôle ``Origin`` anti DNS-rebinding (spec MCP 2025-11-25).

Le contrat de ``current_claims`` est identique à celui d'O2S — ``roles`` est une
**liste**, il n'y a pas de clé ``role`` au singulier. ``tools/referentiels.py``
lit cette forme-là (correctif du décalage relevé au portage : la version
initiale du module lisait ``claims["role"]``, absent, et retombait donc sur un
accès au registre utilisateurs à chaque appel d'outil).
"""

import logging
import os
from contextvars import ContextVar

import jwt
from rhetores_authz import validate_token
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

import user_store

auth_log = logging.getLogger("mcp.auth")

current_claims: ContextVar[dict] = ContextVar("current_claims", default={})

_ALLOWED_ORIGINS = {
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "https://claude.ai").split(",")
    if o.strip()
}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Valide le Bearer token sur chaque requête entrante.

    Les claims validés sont stockés dans ``current_claims`` (ContextVar) et
    accessibles dans tous les tools via ``jwt_auth.current_claims.get()``.
    """

    _BYPASS_PATHS = {"/health"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self._BYPASS_PATHS:
            return await call_next(request)

        # Spec MCP 2025-11-25 — protection DNS rebinding
        origin = request.headers.get("Origin")
        if origin is not None and origin not in _ALLOWED_ORIGINS:
            auth_log.warning(
                "origin_rejected",
                extra={"origin": origin, "path": request.url.path},
            )
            return JSONResponse({"error": "Origin non autorisé"}, status_code=403)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "Authorization header manquant ou invalide"},
                status_code=401,
            )

        token = auth_header.removeprefix("Bearer ")
        try:
            claims = validate_token(token)
        except jwt.ExpiredSignatureError:
            auth_log.warning(
                "auth_failed",
                extra={"reason": "token_expired", "path": request.url.path},
            )
            return JSONResponse({"error": "Token expiré"}, status_code=401)
        except jwt.InvalidTokenError as exc:
            auth_log.warning(
                "auth_failed",
                extra={"reason": str(exc), "path": request.url.path},
            )
            return JSONResponse({"error": f"Token invalide : {exc}"}, status_code=401)

        oid = claims.get("oid") or claims.get("sub", "")
        user = user_store.get_user(oid)
        if user is None:
            auth_log.warning(
                "auth_failed",
                extra={"reason": "user_not_found", "oid": oid, "path": request.url.path},
            )
            return JSONResponse({"error": "Utilisateur non référencé"}, status_code=403)

        # Périmètre reconstruit depuis le store — MÊME FORME QUE O2S.
        # ``cabinet_id`` / ``agence_id`` ne servent pas aux référentiels (ils
        # sont GLOBAUX, transverses aux clients : il n'y a pas de client_id à
        # autoriser, cf. le commentaire d'en-tête de tools/referentiels.py).
        # Ils sont néanmoins conservés pour que la forme des claims reste
        # interchangeable entre les deux serveurs, et parce que l'audit les
        # journalise.
        scope_claims = {
            "sub": oid,
            "email": user.email,
            "cabinet_id": user.cabinet_id,
            "agence_id": user.agence_id,
            "roles": [user.role],
        }
        auth_log.info(
            "auth_success",
            extra={
                "sub": oid,
                "cabinet_id": user.cabinet_id,
                "roles": [user.role],
                "path": request.url.path,
            },
        )
        token_ctx = current_claims.set(scope_claims)
        try:
            return await call_next(request)
        finally:
            current_claims.reset(token_ctx)
