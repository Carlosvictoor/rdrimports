from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from core.extensions import db, limiter
from core.security import sanitize_text, is_honeypot_filled, is_safe_redirect
from models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute; 30 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        # Honeypot — bots preenchem este campo oculto
        if is_honeypot_filled(request.form):
            return redirect(url_for("main.index"))

        email = sanitize_text(request.form.get("email", ""), max_len=254).lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            if not is_safe_redirect(next_page):
                next_page = None
            return redirect(next_page or url_for("main.index"))
        flash("E-mail ou senha inválidos.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/cadastro", methods=["GET", "POST"])
@limiter.limit("5 per hour; 15 per day")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        # Honeypot
        if is_honeypot_filled(request.form):
            flash("Conta criada com sucesso! Bem-vindo à RDR Imports.", "success")
            return redirect(url_for("main.index"))

        name = sanitize_text(request.form.get("name", ""), max_len=100)
        email = sanitize_text(request.form.get("email", ""), max_len=254).lower()
        phone = sanitize_text(request.form.get("phone", ""), max_len=20)
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        error = None
        if not name or not email or not password:
            error = "Preencha todos os campos obrigatórios."
        elif password != confirm:
            error = "As senhas não coincidem."
        elif len(password) < 8:
            error = "A senha deve ter no mínimo 8 caracteres."
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

