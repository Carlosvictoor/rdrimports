import os
from flask import Flask
from config import Config
from core.extensions import db, login_manager, migrate, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Garante que a pasta de uploads existe
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    # Extensões
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para continuar."
    login_manager.login_message_category = "warning"

    # Blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.cart import cart_bp
    from routes.payment import payment_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(cart_bp, url_prefix="/carrinho")
    app.register_blueprint(payment_bp, url_prefix="/pagamento")

    # Cria tabelas no primeiro uso
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
