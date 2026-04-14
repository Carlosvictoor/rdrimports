"""Utilitários de segurança: sanitização de entrada, honeypot, helpers."""
import re
import bleach


def sanitize_text(value: str, *, max_len: int = 500) -> str:
    """Remove HTML/JS do texto e limita o tamanho máximo."""
    cleaned = bleach.clean(str(value), tags=[], strip=True)
    return cleaned[:max_len]


def sanitize_search(value: str) -> str:
    """Sanitiza parâmetro de busca: remove HTML e caracteres perigosos."""
    cleaned = bleach.clean(str(value), tags=[], strip=True)
    # Remove caracteres que podem ser usados em SQL injection / XSS residual
    cleaned = re.sub(r"[<>\"'%;()&+]", "", cleaned)
    return cleaned[:200]


def is_honeypot_filled(form_data) -> bool:
    """Retorna True se o campo honeypot foi preenchido (indica bot).
    O campo 'website' é invisível para humanos (display:none no CSS).
    """
    return bool(form_data.get("website", "").strip())


def is_safe_redirect(url: str) -> bool:
    """Verifica se a URL de redirecionamento é segura (sem open redirect)."""
    if not url:
        return False
    if url.startswith("http") or "//" in url:
        return False
    return True
