"""Identifies which CyberShield client made a request — the web dashboard
or the Phase 6 browser extension — from a single, explicit request header.
Never guessed from User-Agent or any other heuristic."""

from flask import Request

EXTENSION_CLIENT_HEADER = "X-CyberShield-Client"
EXTENSION_CLIENT_VALUE = "extension"


def detect_source(request: Request) -> str:
    if request.headers.get(EXTENSION_CLIENT_HEADER) == EXTENSION_CLIENT_VALUE:
        return "extension"
    return "web"
