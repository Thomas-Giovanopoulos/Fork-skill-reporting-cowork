"""Décorateur d'audit pour les tools MCP (sync et async).

Reprise de ``mcp-o2s-server/tools/_logging.py``. **Une seule divergence**,
documentée ci-dessous : l'allowlist des clés journalisables en clair.
"""

import functools
import inspect
import logging
import time

from jwt_auth import current_claims

audit = logging.getLogger("mcp.audit")

# Allowlist fail-safe des clés de paramètres journalisables EN CLAIR. Toute clé
# absente est considérée potentiellement sensible (PII / données patrimoniales
# client) : sa VALEUR est rédigée, seuls la clé et un marqueur type+taille sont
# conservés. Les clés en `_id` sont des identifiants techniques.
#
# DIVERGENCE ASSUMÉE avec O2S — quatre clés ajoutées : `cible`, `nature`,
# `decision`, `statut`. Ce sont des ÉNUMÉRATIONS fermées, validées par le tool
# avant usage ('acteur'|'gabarit'|..., 'accepte'|'rejete', ...) : elles ne
# peuvent porter aucune donnée client. Les rédiger aurait rendu la piste d'audit
# de l'arbitrage inutilisable — « qui a accepté quoi » est précisément ce qu'on
# doit pouvoir relire, et c'est la contrepartie du privilège admin (D34).
#
# Restent rédigées, à raison : `cle`, `proposition` (contenu extrait d'un
# relevé), `motif`, `commentaire`, `source_document` (nom de fichier client),
# `run_id`.
_ALLOWLIST_KEYS = {"limit", "offset", "date", "cible", "nature", "decision", "statut"}


def _is_allowlisted(key: str) -> bool:
    return key.endswith("_id") or key in _ALLOWLIST_KEYS


def _redact_value(value) -> str:
    """Remplace une valeur sensible par un marqueur non-PII type+taille."""
    type_name = type(value).__name__
    try:
        size = len(value)
    except TypeError:
        size = None
    if size is None:
        return f"<redacted {type_name}>"
    return f"<redacted {type_name}[{size}]>"


def _redact(kwargs: dict) -> dict:
    """Applique la politique d'allowlist fail-safe aux paramètres d'un tool."""
    return {
        key: value if _is_allowlisted(key) else _redact_value(value)
        for key, value in kwargs.items()
    }


def _identity() -> dict:
    claims = current_claims.get()
    return {
        "sub": claims.get("sub", "anonymous"),
        "cabinet_id": claims.get("cabinet_id"),
        "roles": claims.get("roles", []),
    }


def _log_success(func, identity, kwargs, start):
    audit.info(
        "tool_called",
        extra={
            **identity,
            "tool": func.__name__,
            "params": _redact(kwargs),
            "status": "success",
            "duration_ms": round((time.perf_counter() - start) * 1000),
        },
    )


def _log_error(func, identity, kwargs, start, exc):
    audit.error(
        "tool_error",
        extra={
            **identity,
            "tool": func.__name__,
            "params": _redact(kwargs),
            "status": "error",
            "error": str(exc),
            "duration_ms": round((time.perf_counter() - start) * 1000),
        },
        exc_info=True,
    )


def logged(func):
    """Enregistre chaque appel tool : identité, paramètres, durée, statut.

    Gère les tools synchrones et asynchrones. Le contenu de la réponse n'est
    jamais loggé.
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            identity = _identity()
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                _log_success(func, identity, kwargs, start)
                return result
            except Exception as exc:
                _log_error(func, identity, kwargs, start, exc)
                raise
        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        identity = _identity()
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            _log_success(func, identity, kwargs, start)
            return result
        except Exception as exc:
            _log_error(func, identity, kwargs, start, exc)
            raise
    return wrapper
