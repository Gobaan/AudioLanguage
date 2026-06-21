from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.runtime import PROJECT_DIR, validation_store

router = APIRouter()

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleLinkRequest(BaseModel):
    credential: str = Field(min_length=1)
    localParticipantId: str = Field(min_length=1)


@router.get("/api/auth/google/config")
def google_auth_config() -> dict[str, str | bool | None]:
    client_id = google_client_id()
    return {
        "enabled": bool(client_id),
        "clientId": client_id,
    }


@router.post("/api/auth/google/link")
def link_google_account(request: GoogleLinkRequest) -> dict[str, Any]:
    client_id = google_client_id()
    if not client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured")

    try:
        profile = verify_google_id_token(request.credential, client_id)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

    participant_id = google_participant_id(str(profile["sub"]))
    merged_count = validation_store.learning_state.merge_participant(
        request.localParticipantId,
        participant_id,
    )
    return {
        "participantId": participant_id,
        "provider": "google",
        "email": profile.get("email"),
        "name": profile.get("name"),
        "mergedTargetCount": merged_count,
    }


def google_client_id() -> str | None:
    return (
        os.getenv("AUDIO_LANGUAGE_GOOGLE_CLIENT_ID")
        or os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        or google_client_id_from_secret_file()
    )


def google_client_id_from_secret_file() -> str | None:
    config_dir = PROJECT_DIR / "config"
    for path in sorted(config_dir.glob("client_secret_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        oauth_client = payload.get("web") or payload.get("installed") or {}
        client_id = oauth_client.get("client_id")
        if isinstance(client_id, str) and client_id:
            return client_id
    return None


def verify_google_id_token(credential: str, client_id: str) -> dict[str, Any]:
    response = httpx.get(
        GOOGLE_TOKENINFO_URL,
        params={"id_token": credential},
        timeout=5,
    )
    if response.status_code != 200:
        raise ValueError("Google sign-in token could not be verified")

    payload = response.json()
    if payload.get("aud") != client_id:
        raise ValueError("Google sign-in token was issued for a different client")
    if not payload.get("sub"):
        raise ValueError("Google sign-in token is missing a stable account id")
    if payload.get("email_verified") not in {True, "true", "True", "1", 1}:
        raise ValueError("Google account email is not verified")
    return payload


def google_participant_id(google_subject: str) -> str:
    digest = hashlib.sha256(google_subject.encode("utf-8")).hexdigest()[:16]
    return f"Google-{digest}"
