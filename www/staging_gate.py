"""Staging access gate (edrefcard2-dev.l0l.fr).

Active only when ACCESS_TOKEN is set (staging environment in Dokploy, never in
production). Without a valid cookie, a page request is redirected to /acces
(a real password field, password-manager friendly); other requests get a 403.
Every staging response carries X-Robots-Tag: noindex.

The password is only stored in the staging environment variables, never in
the repository.
"""
import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

from flask import Flask, Response, redirect, render_template_string, request

COOKIE = "er_access"
COOKIE_MAX_AGE = 60 * 60 * 24 * 90
NOINDEX = "noindex, nofollow, noarchive"
FREE_PATHS = {"/acces", "/robots.txt", "/favicon.ico"}
MAX_FAILURES = 10
WINDOW_S = 10 * 60

# Per-worker failure counter (gunicorn runs 4 workers: the effective limit is
# at most 4x MAX_FAILURES per window, still far from a usable brute force).
_failures: dict[str, tuple[int, float]] = {}

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Restricted access</title>
<style>
body{font-family:system-ui,sans-serif;background:#111;color:#eee;display:grid;place-items:center;min-height:100vh;margin:0}
main{width:min(22rem,90vw)}h1{font-size:1.8rem;margin:.3rem 0 1rem}
p{opacity:.8;line-height:1.5}form{display:flex;flex-direction:column;gap:.8rem;margin-top:1.2rem}
input[type=password]{padding:.7rem;border-radius:6px;border:1px solid #555;background:#1b1b1b;color:#eee;font-size:1rem}
button{padding:.7rem;border:0;border-radius:6px;background:#f07b05;color:#111;font-weight:700;font-size:1rem;cursor:pointer}
.err{color:#ff7a6b}.hidden{position:absolute;left:-9999px}
</style></head><body><main>
<p>EDRefCard · staging</p><h1>Restricted access</h1>
<p>This version of the site is not public. Enter the access password.</p>
<form method="post" action="/acces">
<input type="hidden" name="suite" value="{{ suite }}">
<input class="hidden" type="text" name="identifiant" autocomplete="username" value="staging" tabindex="-1" aria-hidden="true">
<label>Password<br><input type="password" name="cle" autocomplete="current-password" required autofocus></label>
{% if erreur %}<p class="err" role="alert">Wrong password.</p>{% endif %}
<button type="submit">Enter</button>
</form></main></body></html>"""


def _active() -> bool:
    return bool(os.environ.get("ACCESS_TOKEN"))


def _valid(key: str | None) -> bool:
    expected = os.environ.get("ACCESS_TOKEN")
    if not expected or not key:
        return False
    a = hashlib.sha256(key.encode()).digest()
    b = hashlib.sha256(expected.encode()).digest()
    return hmac.compare_digest(a, b)


def _safe_next(value: str | None) -> str:
    """Internal path only: never an external URL ("//x.com", "/\\x.com", "https://...").

    Browsers treat a backslash like a slash, so "/\\x.com" would leave the site.
    """
    if (not value or not value.startswith("/") or value.startswith("/acces")
            or "\\" in value or value.startswith("//") or any(c < " " for c in value)):
        return "/"
    return value


def _client_ip() -> str:
    # Behind Cloudflare + Traefik: remote_addr is the proxy, not the visitor.
    return (
        request.headers.get("CF-Connecting-IP")
        or (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        or request.remote_addr
        or "unknown"
    )


def _too_many(ip: str) -> bool:
    count, start = _failures.get(ip, (0, 0.0))
    return time.time() - start < WINDOW_S and count >= MAX_FAILURES


def _note_failure(ip: str) -> None:
    count, start = _failures.get(ip, (0, 0.0))
    now = time.time()
    _failures[ip] = (1, now) if now - start > WINDOW_S else (count + 1, start)


def register(app: Flask) -> None:
    """Install the gate. Must be called before any other before_request hook."""

    @app.before_request
    def staging_gate():
        if not _active():
            return None
        if request.path == "/acces":
            return _acces()
        if _valid(request.cookies.get(COOKIE)) or request.path in FREE_PATHS:
            return None
        is_page = request.method == "GET" and "." not in request.path.rsplit("/", 1)[-1] and not request.path.startswith("/api/")
        if is_page:
            # Relative Location: behind Traefik the absolute URL would carry the
            # container's internal address.
            full = request.full_path.rstrip("?")
            return Response(status=307, headers={"Location": "/acces?" + urlencode({"suite": full})})
        return Response("Restricted access.", status=403)

    @app.after_request
    def staging_noindex(response):
        if _active():
            response.headers["X-Robots-Tag"] = NOINDEX
        return response


def _acces():
    if request.method == "GET":
        return render_template_string(
            PAGE, suite=_safe_next(request.args.get("suite")), erreur=bool(request.args.get("erreur"))
        )
    ip = _client_ip()
    if _too_many(ip):
        return Response("Too many attempts. Try again in a few minutes.", status=429)
    suite = _safe_next(request.form.get("suite"))
    if not _valid(request.form.get("cle")):
        _note_failure(ip)
        return Response(status=303, headers={"Location": "/acces?" + urlencode({"erreur": "1", "suite": suite})})
    _failures.pop(ip, None)
    response = redirect(suite, code=303)
    response.autocorrect_location_header = False
    response.set_cookie(
        COOKIE, os.environ["ACCESS_TOKEN"], max_age=COOKIE_MAX_AGE, httponly=True, secure=True, samesite="Lax", path="/"
    )
    return response
