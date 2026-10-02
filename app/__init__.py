from pathlib import Path

from flask import Flask, render_template, send_from_directory

from app.config import Config
from app.extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        instance_relative_config=False,
    )
    app.config.from_object(config_class)

    # Absolute upload folder under project root
    upload = Path(app.config["UPLOAD_FOLDER"])
    if not upload.is_absolute():
        upload = Path(app.root_path).parent / upload
    upload.mkdir(parents=True, exist_ok=True)
    (upload / "covers").mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.blueprints import auth, cart, catalog, main

    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(catalog.bp)
    app.register_blueprint(cart.bp)

    # SQLite is created automatically on startup; no migration tool is needed.
    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_cart():
        from app.services.cart import Cart

        return {"cart": Cart()}

    @app.route("/media/<path:filename>")
    def media_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    # CLI commands
    @app.cli.command("seed")
    def seed_command():
        """Seed products and create admin user."""
        from seed import run_seed

        run_seed(clear=True)

    @app.cli.command("create-admin")
    def create_admin_command():
        """Create staff user admin / admin12345."""
        from app.models import User

        user = User.query.filter_by(username="admin").first()
        if user:
            user.is_staff = True
            user.set_password("admin12345")
            db.session.commit()
            print("Updated existing admin (password reset to admin12345)")
        else:
            user = User(username="admin", email="admin@garage.local", is_staff=True)
            user.set_password("admin12345")
            db.session.add(user)
            db.session.commit()
            print("Created admin / admin12345")

    return app
