"""
Auth mòdul — autenticació simple amb cookie de sessió.

Fluxe:
  POST /api/v1/auth/login   → valida contrasenya → posa cookie 30 dies
  GET  /api/v1/auth/status  → 200 si autenticat, 401 si no

El token de sessió és determinista (hash de password + SECRET_KEY),
de manera que sobreviu reinicis del servidor sense invalïdar sessions
actives dels usuaris.
"""
import hashlib
import os

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE_NAME    = "wp_session"
COOKIE_MAX_AGE = 30 * 24 * 3600  # 30 dies


def _session_token() -> str:
    """Token determinista derivat de les variables d'entorn.
    Canvia només si es canvia la contrasenya o el SECRET_KEY."""
    password   = os.getenv("APP_PASSWORD", "")
    secret_key = os.getenv("SECRET_KEY", "")
    return hashlib.sha256(f"wp:{password}:{secret_key}".encode()).hexdigest()


# Calculat una sola vegada en arrencar l'aplicació
VALID_TOKEN = _session_token()


def is_authenticated(request: Request) -> bool:
    return request.cookies.get(COOKIE_NAME) == VALID_TOKEN


# ─── Endpoints ────────────────────────────────────────────────────────────────

class LoginBody(BaseModel):
    password: str


@router.post("/login")
def login(body: LoginBody, response: Response):
    """Valida la contrasenya i estableix la cookie de sessió si és correcta."""
    expected = os.getenv("APP_PASSWORD", "")
    if not expected:
        return JSONResponse(status_code=500, content={"detail": "APP_PASSWORD no configurada"})

    if body.password != expected:
        return JSONResponse(status_code=401, content={"detail": "Contrasenya incorrecta"})

    response.set_cookie(
        key=COOKIE_NAME,
        value=VALID_TOKEN,
        max_age=COOKIE_MAX_AGE,
        httponly=True,   # no accessible per JS
        secure=True,     # només via HTTPS
        samesite="strict",
    )
    return {"ok": True}


@router.get("/status")
def status(request: Request):
    """Comprova si la sessió actual és vàlida."""
    if is_authenticated(request):
        return {"authenticated": True}
    return JSONResponse(status_code=401, content={"authenticated": False})
