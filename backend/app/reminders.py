from __future__ import annotations

import json
import logging
import os
import time
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

DEFAULT_REMINDER_TIME = "22:00"
REMINDER_CHECK_SECONDS = 60
UTC_TIMEZONE_KEYS = {"UTC", "Etc/UTC", "Etc/GMT", "GMT"}


class ReminderDependencyError(RuntimeError):
    """Raised when optional Web Push dependencies are not installed."""


@dataclass(frozen=True, slots=True)
class ReminderSubscription:
    participant_id: str
    endpoint: str
    subscription: dict[str, Any]
    time: str
    timezone: str
    enabled: bool = True
    last_sent_date: str | None = None


class ReminderStore:
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.path = storage_dir / "daily_reminder_subscriptions.json"
        self.key_path = storage_dir / "daily_reminder_vapid_private.pem"
        self._lock = threading.RLock()

    def public_key(self) -> str:
        try:
            from cryptography.hazmat.primitives import serialization
        except ModuleNotFoundError as error:
            raise ReminderDependencyError("Web Push dependencies are not installed") from error

        vapid = self._load_or_create_vapid()
        raw_public_key = vapid.public_key.public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )
        return base64url(raw_public_key)

    def private_key_pem(self) -> str:
        return self._load_or_create_vapid().private_pem().decode("utf-8")

    def upsert(self, subscription: ReminderSubscription) -> dict[str, Any]:
        with self._lock:
            payload = self._read_payload()
            subscriptions = [
                item
                for item in payload["subscriptions"]
                if item.get("endpoint") != subscription.endpoint
            ]
            existing = next(
                (
                    item
                    for item in payload["subscriptions"]
                    if item.get("endpoint") == subscription.endpoint
                ),
                {},
            )
            subscriptions.append(
                {
                    "participantId": subscription.participant_id,
                    "endpoint": subscription.endpoint,
                    "subscription": subscription.subscription,
                    "time": subscription.time,
                    "timezone": subscription.timezone,
                    "enabled": subscription.enabled,
                    "lastSentDate": existing.get("lastSentDate") or subscription.last_sent_date,
                }
            )
            payload["subscriptions"] = subscriptions
            self._write_payload(payload)
        return {"ok": True}

    def unsubscribe(self, endpoint: str) -> dict[str, Any]:
        with self._lock:
            payload = self._read_payload()
            payload["subscriptions"] = [
                item for item in payload["subscriptions"] if item.get("endpoint") != endpoint
            ]
            self._write_payload(payload)
        return {"ok": True}

    def due_subscriptions(self, now_utc: datetime | None = None) -> list[ReminderSubscription]:
        now = now_utc or datetime.now(tz=UTC)
        due: list[ReminderSubscription] = []
        with self._lock:
            for item in self._read_payload()["subscriptions"]:
                subscription = subscription_from_payload(item)
                if subscription and is_due(subscription, now):
                    due.append(subscription)
        return due

    def mark_sent(self, endpoint: str, local_date: str) -> None:
        with self._lock:
            payload = self._read_payload()
            for item in payload["subscriptions"]:
                if item.get("endpoint") == endpoint:
                    item["lastSentDate"] = local_date
                    break
            self._write_payload(payload)

    def _load_or_create_vapid(self):
        try:
            from py_vapid import Vapid01
        except ModuleNotFoundError as error:
            raise ReminderDependencyError("Web Push dependencies are not installed") from error

        with self._lock:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            vapid = Vapid01()
            if self.key_path.exists():
                try:
                    return Vapid01.from_pem(self.key_path.read_bytes())
                except ValueError as error:
                    logger.warning("Stored VAPID private key is invalid; generating a fresh reminder key.")
                    backup_path = self.key_path.with_name(
                        f"{self.key_path.name}.invalid-{int(time.time())}"
                    )
                    self.key_path.replace(backup_path)
            vapid.generate_keys()
            self.key_path.write_bytes(vapid.private_pem())
            return vapid

    def _read_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"subscriptions": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Reminder subscription store is invalid; treating it as empty.")
            return {"subscriptions": []}
        if not isinstance(payload, dict) or not isinstance(payload.get("subscriptions"), list):
            return {"subscriptions": []}
        return payload

    def _write_payload(self, payload: dict[str, Any]) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".json.tmp")
        temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temp_path.replace(self.path)


class ReminderSender:
    def __init__(self, store: ReminderStore):
        self.store = store

    def send_due_reminders(self, now_utc: datetime | None = None) -> int:
        sent = 0
        for subscription in self.store.due_subscriptions(now_utc):
            local_date = local_date_for(subscription, now_utc)
            try:
                self._send(subscription)
            except ReminderDependencyError:
                logger.warning("Daily reminders are disabled because Web Push dependencies are missing.")
                return sent
            except Exception as error:
                if is_expired_push_subscription_error(error):
                    self.store.unsubscribe(subscription.endpoint)
                logger.warning("Daily reminder push failed for %s: %s", subscription.participant_id, error)
                continue
            self.store.mark_sent(subscription.endpoint, local_date)
            sent += 1
        return sent

    def _send(self, subscription: ReminderSubscription) -> None:
        try:
            from pywebpush import webpush
        except ModuleNotFoundError as error:
            raise ReminderDependencyError("Web Push dependencies are not installed") from error

        webpush(
            subscription_info=subscription.subscription,
            data=json.dumps(
                {
                    "title": "Audio Language",
                    "body": "Quick practice check-in?",
                    "url": "/gobi-home",
                }
            ),
            vapid_private_key=self.store.private_key_pem(),
            vapid_claims={"sub": os.environ.get("AUDIO_LANGUAGE_VAPID_SUBJECT", "mailto:reminders@gobaan.com")},
        )


class ReminderScheduler:
    def __init__(self, sender: ReminderSender, *, interval_seconds: int = REMINDER_CHECK_SECONDS):
        self.sender = sender
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="daily-reminder-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.wait(self.interval_seconds):
            try:
                self.sender.send_due_reminders()
            except Exception:
                logger.exception("Daily reminder scheduler failed.")


def subscription_from_payload(item: Any) -> ReminderSubscription | None:
    if not isinstance(item, dict):
        return None
    endpoint = str(item.get("endpoint") or "")
    subscription = item.get("subscription")
    participant_id = str(item.get("participantId") or "Learner")
    reminder_time = str(item.get("time") or DEFAULT_REMINDER_TIME)
    timezone = str(item.get("timezone") or "")
    if not endpoint or not isinstance(subscription, dict):
        return None
    if not is_valid_reminder_time(reminder_time) or not is_valid_timezone(timezone):
        return None
    return ReminderSubscription(
        participant_id=participant_id,
        endpoint=endpoint,
        subscription=subscription,
        time=reminder_time,
        timezone=timezone,
        enabled=item.get("enabled") is not False,
        last_sent_date=str(item.get("lastSentDate") or "") or None,
    )


def is_due(subscription: ReminderSubscription, now_utc: datetime) -> bool:
    if not subscription.enabled:
        return False
    local_now = now_utc.astimezone(timezone_for_key(subscription.timezone))
    local_date = local_now.date().isoformat()
    if subscription.last_sent_date == local_date:
        return False
    return local_now.strftime("%H:%M") >= subscription.time


def local_date_for(subscription: ReminderSubscription, now_utc: datetime | None = None) -> str:
    now = now_utc or datetime.now(tz=UTC)
    return now.astimezone(timezone_for_key(subscription.timezone)).date().isoformat()


def is_valid_reminder_time(value: str) -> bool:
    try:
        hours_text, minutes_text = value.split(":", 1)
        hours = int(hours_text)
        minutes = int(minutes_text)
    except ValueError:
        return False
    return 0 <= hours <= 23 and 0 <= minutes <= 59 and value == f"{hours:02d}:{minutes:02d}"


def is_valid_timezone(value: str) -> bool:
    try:
        timezone_for_key(value)
    except ZoneInfoNotFoundError:
        return False
    return True


def timezone_for_key(value: str) -> tzinfo:
    if value in UTC_TIMEZONE_KEYS:
        return UTC
    return ZoneInfo(value)


def base64url(value: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def is_expired_push_subscription_error(error: Exception) -> bool:
    status_code = getattr(getattr(error, "response", None), "status_code", None)
    return status_code in {404, 410}
