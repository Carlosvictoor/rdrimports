from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from core.extensions import db
from models.user import User
import time

auth_bp = Blueprint("auth", __name__)

# ── Rate limiting simples via sessão (5 tentativas em 5 min) ──
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300


def _check_rate_limit() -> bool:
    """Retorna True se o IP pode tentar. Incrementa contador."""
    now = time.time()
    key = "login_attempts"
    key_time = "login_lockout_until"

    lockout_until = session.get(key_time, 0)
    if now < lockout_until:
        return False

    attempts = session.get(key, [])
    # Remove tentativas antigas (> 5 min)
    attempts = [t for t in attempts if now - t < _LOCKOUT_SECONDS]
    attempts.append(now)
    session[key] = attempts

    if len(attempts) >= _MAX_ATTEMPTS:
        session[key_time] = now + _LOCKOUT_SECONDS
        session[key] = []
        return False
    return True


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        if not _check_rate_limit():
            flash("Muitas tentativas de login. Aguarde 5 minutos.", "danger")
            return render_template("auth/login.html")

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session.pop("login_attempts", None)
            session.pop("login_lockout_until", None)
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            # Evita open redirect — só permite caminhos internos
            if next_page and (next_page.startswith("http") or "//" in next_page):
                next_page = None
            return redirect(next_page or url_for("main.index"))
        flash("E-mail ou senha inválidos.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        error = None
        if not name or not email or not password:
            error = "Preencha todos os campos obrigatórios."
        elif password != confirm:
            error = "As senhas não coincidem."
        elif len(password) < 6:
            error = "A senha deve ter no mínimo 6 caracteres."
        elif User.query.filter_by(email=email).first():
            error = "E-mail já cadastrado."

        if error:
            flash(error, "danger")
        else:
            user = User(name=name, email=email, phone=phone)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Conta criada com sucesso! Bem-vindo à RDR Imports.", "success")
            return redirect(url_for("main.index"))

    return render_template("auth/register.html")


@auth_bp.route("/sair")
@login_required
def logout():
    logout_user()
    flash("Você saiu da conta.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/minha-conta")
@login_required
def account():
    return render_template("auth/account.html")
