from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.reminders import ReminderDependencyError, ReminderSubscription, is_valid_reminder_time, is_valid_timezone
from app.runtime import reminder_store

router = APIRouter()


class ReminderSubscribeRequest(BaseModel):
    participantId: str = Field(min_length=1, max_length=80)
    time: str = Field(default="22:00")
    timezone: str = Field(min_length=1, max_length=80)
    subscription: dict[str, Any]


class ReminderUnsubscribeRequest(BaseModel):
    endpoint: str = Field(min_length=1)


@router.get("/api/reminders/public-key")
def get_reminder_public_key():
    try:
        public_key = reminder_store.public_key()
    except ReminderDependencyError as error:
        raise HTTPException(
            status_code=503,
            detail="Web Push dependencies are not installed. Run pip install -r requirements.txt.",
        ) from error
    return {"publicKey": public_key, "defaultTime": "22:00"}


@router.post("/api/reminders/subscriptions")
def subscribe_to_reminders(request: ReminderSubscribeRequest):
    endpoint = str(request.subscription.get("endpoint") or "")
    if not endpoint:
        raise HTTPException(status_code=400, detail="Push subscription endpoint is required")
    if not is_valid_reminder_time(request.time):
        raise HTTPException(status_code=400, detail="Reminder time must use HH:MM format")
    if not is_valid_timezone(request.timezone):
        raise HTTPException(status_code=400, detail="Reminder timezone is invalid")

    return reminder_store.upsert(
        ReminderSubscription(
            participant_id=request.participantId,
            endpoint=endpoint,
            subscription=request.subscription,
            time=request.time,
            timezone=request.timezone,
        )
    )


@router.post("/api/reminders/unsubscribe")
def unsubscribe_from_reminders(request: ReminderUnsubscribeRequest):
    return reminder_store.unsubscribe(request.endpoint)
