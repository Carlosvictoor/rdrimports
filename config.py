import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'rdrimports.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # Mercado Pago
    MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")
    MP_PUBLIC_KEY = os.environ.get("MP_PUBLIC_KEY", "")

    # URL base (usada nos webhooks do MP)
    BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")

    ITEMS_PER_PAGE = 12

    # ── Segurança de sessão ────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 604800  # 7 dias
    WTF_CSRF_TIME_LIMIT = 3600         # CSRF token expira em 1h

    # SESSION_COOKIE_SECURE deve ser True em produção (HTTPS).
    # Controlado via env para não quebrar desenvolvimento HTTP.
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"

    # ── Rate limiting ──────────────────────────────────────────────────────
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_DEFAULT = ["300 per day", "100 per hour"]
