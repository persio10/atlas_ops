from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from atlas_ops import __version__

from .config import BackendSettings
from .db import SignalStore

router = APIRouter(prefix="/api")


def get_settings(router_settings: BackendSettings | None = None) -> BackendSettings:
    if router_settings is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="settings missing")
    return router_settings


def get_store(store: SignalStore | None = None) -> SignalStore:
    if store is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="store missing")
    return store


def _require_token(shared_token: str, provided: str | None) -> None:
    if shared_token and provided != shared_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


@router.get("/health")
def health(settings: BackendSettings = Depends(get_settings)) -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/sites")
def list_sites(settings: BackendSettings = Depends(get_settings)) -> dict:
    return {"sites": [site.model_dump() for site in settings.sites]}


@router.get("/signals")
def list_signals(store: SignalStore = Depends(get_store)) -> dict:
    return {"signals": store.list_signals()}


@router.post("/signals")
def add_signal(
    payload: dict,
    store: SignalStore = Depends(get_store),
    settings: BackendSettings = Depends(get_settings),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    token = authorization.replace("Bearer ", "", 1) if authorization else None
    _require_token(settings.shared_token, token)
    name = payload.get("name", "unknown")
    status = payload.get("status", "unknown")
    details = payload.get("details")
    store.add_signal(name=name, status=status, details=details)
    return {"ok": True}


@router.get("/runbooks")
def list_runbooks(settings: BackendSettings = Depends(get_settings)) -> dict:
    runbooks = [
        {
            "name": "restart-container",
            "description": "Restart a misbehaving service container",
            "steps": ["docker ps", "docker restart <container>"]
            + ([f"notify {site.name}"] if settings.sites else []),
        }
    ]
    return {"runbooks": runbooks}


@router.get("/suggestions")
def list_suggestions(store: SignalStore = Depends(get_store)) -> dict:
    suggestions = []
    for signal in store.recent_signals(limit=5):
        suggestions.append(
            {
                "title": f"Investigate {signal['name']}",
                "body": signal["details"].get("message") if isinstance(signal.get("details"), dict) else None,
            }
        )
    return {"suggestions": suggestions}

