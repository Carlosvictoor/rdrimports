import os
from flask import Flask, render_template
from config import Config
from core.extensions import db, login_manager, migrate, csrf, limiter


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Garante que a pasta de uploads existe
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    # ── Extensões base ─────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para continuar."
    login_manager.login_message_category = "warning"

    # ── Flask-Talisman (headers de segurança HTTP) ─────────────────────────
    from flask_talisman import Talisman
    is_prod = os.environ.get("FLASK_ENV") == "production"

    _csp = {
        "default-src": "'self'",
        "script-src": [
            "'self'",
            "'unsafe-inline'",          # necessário para snippets inline do MP
            "https://sdk.mercadopago.com",
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "https://fonts.googleapis.com",
            "https://cdn.jsdelivr.net",
        ],
        "font-src": [
            "'self'",
            "https://fonts.gstatic.com",
            "https://cdn.jsdelivr.net",
        ],
        "img-src": ["'self'", "data:", "https:"],
        "connect-src": ["'self'", "https://api.mercadopago.com"],
        "frame-src": [
            "'self'",
            "https://www.mercadopago.com",
            "https://www.mercadopago.com.br",
        ],
        "object-src": "'none'",
        "base-uri": "'self'",
        "form-action": "'self'",
    }

    Talisman(
        app,
        force_https=is_prod,
        strict_transport_security=is_prod,
        strict_transport_security_max_age=31536000,
        content_security_policy=_csp,
        session_cookie_secure=is_prod,
        session_cookie_http_only=True,
        x_content_type_options=True,
        frame_options="DENY",
        referrer_policy="strict-origin-when-cross-origin",
    )

    # ── Blueprints ─────────────────────────────────────────────────────────
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.cart import cart_bp
    from routes.payment import payment_bp
    from routes.reviews import reviews_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(cart_bp, url_prefix="/carrinho")
    app.register_blueprint(payment_bp, url_prefix="/pagamento")
    app.register_blueprint(reviews_bp)

    # ── Handlers de erro ───────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # ── Cria tabelas no primeiro uso ───────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    """Cria conta admin padrão se não existir."""
    from models.user import User
    from core.extensions import db
    import os

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@rdrimports.com")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")

    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            name="Admin",
            email=admin_email,
            is_admin=True,
        )
        admin.set_password(admin_pass)
        db.session.add(admin)
        db.session.commit()

        if admin_pass == "admin123":
            import warnings
            warnings.warn(
                "\n⚠️  ATENÇÃO: Admin criado com senha padrão 'admin123'. "
                "Defina ADMIN_PASSWORD no .env antes de publicar!",
                stacklevel=2,
            )


if __name__ == "__main__":
    app = create_app()
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host='0.0.0.0', debug=debug_mode)
