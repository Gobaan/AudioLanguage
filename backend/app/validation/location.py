from __future__ import annotations

import ipaddress
from typing import Any

from fastapi import Request

COUNTRY_CODE_HEADERS = (
    "cf-ipcountry",
    "x-vercel-ip-country",
    "x-country-code",
    "cloudfront-viewer-country",
)


def client_ip_from_request(request: Request) -> str:
    """Resolve the best-effort client IP from common proxy headers."""
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        for candidate in forwarded_for.split(","):
            normalized = normalize_ip(candidate)
            if normalized:
                return normalized

    real_ip = normalize_ip(request.headers.get("x-real-ip", ""))
    if real_ip:
        return real_ip

    if request.client and request.client.host:
        return normalize_ip(request.client.host) or ""

    return ""


def location_flag_from_ip(raw_ip: str) -> str:
    """Return a rough, privacy-safe location/network label from an IP."""
    ip_text = normalize_ip(raw_ip)
    if not ip_text:
        return "❓ Unknown"

    try:
        parsed = ipaddress.ip_address(ip_text)
    except ValueError:
        return "❓ Unknown"

    if parsed.is_loopback:
        return "🏠 Localhost"

    if isinstance(parsed, ipaddress.IPv4Address):
        octets = ip_text.split(".")
        if parsed.is_private and len(octets) == 4:
            return f"🏡 LAN {octets[0]}.{octets[1]}.{octets[2]}.*"
        if parsed.is_link_local:
            return "🔗 Link-local"
        if len(octets) == 4:
            return f"🌍 Public {octets[0]}.{octets[1]}.*.*"
        return "🌍 Public"

    # IPv6
    if parsed.is_private:
        return "🏡 LAN IPv6"
    if parsed.is_link_local:
        return "🔗 Link-local IPv6"
    return "🌍 Public IPv6"


def enrich_session_metadata_with_location(metadata: dict[str, Any], request: Request) -> dict[str, Any]:
    client_ip = client_ip_from_request(request)
    location_flag = location_flag_from_country_code(request) or location_flag_from_ip(client_ip)
    return {
        **metadata,
        "clientIp": client_ip or None,
        "locationFlag": location_flag,
    }


def location_flag_from_country_code(request: Request) -> str | None:
    for header in COUNTRY_CODE_HEADERS:
        country_code = normalize_country_code(request.headers.get(header, ""))
        if country_code:
            return f"{country_flag(country_code)} {country_code}"
    return None


def normalize_country_code(value: str) -> str:
    code = str(value or "").strip().upper()
    if len(code) != 2 or not code.isalpha() or code == "XX":
        return ""
    return code


def country_flag(country_code: str) -> str:
    return "".join(chr(0x1F1E6 + ord(char) - ord("A")) for char in country_code)


def normalize_ip(value: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""

    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]

    if cleaned.startswith("::ffff:"):
        cleaned = cleaned[7:]

    return cleaned
