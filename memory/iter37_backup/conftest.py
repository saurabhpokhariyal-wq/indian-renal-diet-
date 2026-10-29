"""Test-session helpers.

The login endpoint is rate-limited to 5/minute per client IP, and ~26 test
modules each log in through the same ingress IP — so a full run used to fail
with 429s that had nothing to do with the code under test. Cache successful
login responses per (email, password) for the session so every module reuses
one real token. Failed logins (wrong password, 401/422) are never cached and
still hit the server.
"""
from __future__ import annotations

import json

import pytest
import requests

_cache: dict = {}
_orig_post = requests.post
_orig_session_post = requests.Session.post


def _key(url, kwargs):
    if not str(url).rstrip("/").endswith("/api/auth/login"):
        return None
    body = kwargs.get("json")
    if body is None and kwargs.get("data"):
        try:
            body = json.loads(kwargs["data"])
        except (TypeError, ValueError):
            return None
    if not isinstance(body, dict):
        return None
    return (body.get("email"), body.get("password"))


def _cached(send, url, kwargs):
    key = _key(url, kwargs)
    if key and key in _cache:
        return _cache[key]
    resp = send()
    if key and resp.status_code == 200:
        _cache[key] = resp
    return resp


@pytest.fixture(autouse=True, scope="session")
def _share_login_tokens():
    def post(url, *a, **kw):
        return _cached(lambda: _orig_post(url, *a, **kw), url, kw)

    def session_post(self, url, *a, **kw):
        return _cached(lambda: _orig_session_post(self, url, *a, **kw), url, kw)

    requests.post = post
    requests.Session.post = session_post
    yield
    requests.post = _orig_post
    requests.Session.post = _orig_session_post
