import os
import logging
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from core.extensions import db, limiter
from core.security import sanitize_text
from models.category import Category
from models.product import Product
from models.order import Order
from models.user import User

admin_bp = Blueprint("admin", __name__)

ALLOWED = {"png", "jpg", "jpeg", "webp"}

_logger = logging.getLogger("rdrimports.admin")


def admin_required(f):
    @wraps(f)
    @login_required
    @limiter.limit("200 per hour")
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            _logger.warning(
                "Acesso negado ao admin — usuário: %s IP: %s",
                getattr(current_user, "email", "anônimo"),
                request.remote_addr,
            )
            # Retorna 404 para não revelar que o painel existe
            from flask import abort
            abort(404)
        return f(*args, **kwargs)
    return decorated


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED


def _save_image(file):
    if file and _allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Prefixo único para evitar colisão
        import uuid
        unique = uuid.uuid4().hex[:8]
        filename = f"{unique}_{filename}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        return filename
    return None


# ─── Dashboard ────────────────────────────────────────────────────────────────

@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "products": Product.query.count(),
        "categories": Category.query.count(),
        "orders": Order.query.count(),
        "users": User.query.count(),
        "revenue": db.session.query(db.func.sum(Order.total)).filter_by(status="pago").scalar() or 0,
        "pending_orders": Order.query.filter_by(status="pendente").count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, recent_orders=recent_orders)


# ─── Categorias ───────────────────────────────────────────────────────────────

@admin_bp.route("/categorias")
@admin_required
def categories():
    cats = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", categories=cats)


@admin_bp.route("/categorias/nova", methods=["GET", "POST"])
@admin_required
def category_new():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        desc = request.form.get("description", "").strip()
        if not name:
            flash("Nome é obrigatório.", "danger")
        elif Category.query.filter_by(name=name).first():
            flash("Categoria já existe.", "danger")
        else:
            slug = Category.make_slug(name)
            # garante slug único
            base_slug = slug
            counter = 1
            while Category.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            image = _save_image(request.files.get("image"))
            cat = Category(name=name, slug=slug, description=desc, image=image)
            db.session.add(cat)
            db.session.commit()
            flash("Categoria criada!", "success")
            return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", category=None)


@admin_bp.route("/categorias/<int:cat_id>/editar", methods=["GET", "POST"])
@admin_required
def category_edit(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Nome é obrigatório.", "danger")
        else:
            existing = Category.query.filter_by(name=name).first()
            if existing and existing.id != cat.id:
                flash("Já existe uma categoria com esse nome.", "danger")
            else:
                cat.name = name
                cat.description = request.form.get("description", "").strip()
                image = _save_image(request.files.get("image"))
                if image:
                    cat.image = image
                db.session.commit()
                flash("Categoria atualizada!", "success")
                return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", category=cat)


@admin_bp.route("/categorias/<int:cat_id>/excluir", methods=["POST"])
@admin_required
def category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.products:
        flash("Não é possível excluir uma categoria com produtos.", "danger")
    else:
        db.session.delete(cat)
        db.session.commit()
        flash("Categoria excluída.", "info")
    return redirect(url_for("admin.categories"))


# ─── Produtos ─────────────────────────────────────────────────────────────────

@admin_bp.route("/produtos")
@admin_required
def products():
    q = request.args.get("q", "").strip()
    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    items = query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products.html", products=items, q=q)


@admin_bp.route("/produtos/novo", methods=["GET", "POST"])
@admin_required
def product_new():
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        prod = _product_from_form(None)
        if prod:
            db.session.add(prod)
            db.session.commit()
            flash("Produto cadastrado!", "success")
            return redirect(url_for("admin.products"))
    return render_template("admin/product_form.html", product=None, categories=categories)


@admin_bp.route("/produtos/<int:prod_id>/editar", methods=["GET", "POST"])
@admin_required
def product_edit(prod_id):
    prod = Product.query.get_or_404(prod_id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        updated = _product_from_form(prod)
        if updated:
            db.session.commit()
            flash("Produto atualizado!", "success")
            return redirect(url_for("admin.products"))
    return render_template("admin/product_form.html", product=prod, categories=categories)


@admin_bp.route("/produtos/<int:prod_id>/excluir", methods=["POST"])
@admin_required
def product_delete(prod_id):
    prod = Product.query.get_or_404(prod_id)
    prod.active = False
    db.session.commit()
    flash("Produto desativado.", "info")
    return redirect(url_for("admin.products"))


def _product_from_form(existing):
    """Lê o formulário e retorna produto (novo ou atualizado). Retorna None em erro."""
    name = request.form.get("name", "").strip()
    price_str = request.form.get("price", "0")
    stock_str = request.form.get("stock", "0")

    if not name:
        flash("Nome é obrigatório.", "danger")
        return None
    try:
        price = float(price_str)
        stock = int(stock_str)
    except ValueError:
        flash("Preço ou estoque inválido.", "danger")
        return None

    original_price_str = request.form.get("original_price", "").strip()
    original_price = float(original_price_str) if original_price_str else None

    slug = Product.make_slug(name)
    base_slug = slug
    counter = 1
    query = Product.query.filter_by(slug=slug)
    if existing:
        query = query.filter(Product.id != existing.id)
    while query.first():
        slug = f"{base_slug}-{counter}"
        counter += 1
        query = Product.query.filter_by(slug=slug)
        if existing:
            query = query.filter(Product.id != existing.id)

    prod = existing or Product()
    prod.name = name
    prod.slug = slug
    prod.description = request.form.get("description", "").strip()
    prod.price = price
    prod.original_price = original_price
    prod.stock = stock
    prod.brand = request.form.get("brand", "").strip()
    prod.volume = request.form.get("volume", "").strip()
    prod.featured = bool(request.form.get("featured"))
    prod.active = bool(request.form.get("active", True))

    category_id = request.form.get("category_id")
    prod.category_id = int(category_id) if category_id else None

    image = _save_image(request.files.get("image"))
    if image:
        prod.image = image

    return prod


# ─── Pedidos ──────────────────────────────────────────────────────────────────

@admin_bp.route("/pedidos")
@admin_required
def orders():
    status_filter = request.args.get("status", "")
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    items = query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=items, status_filter=status_filter)


@admin_bp.route("/pedidos/<int:order_id>")
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("admin/order_detail.html", order=order)


@admin_bp.route("/pedidos/<int:order_id>/status", methods=["POST"])
@admin_required
def order_update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", "")
    valid = [Order.STATUS_PENDING, Order.STATUS_PAID, Order.STATUS_SHIPPED,
             Order.STATUS_DELIVERED, Order.STATUS_CANCELLED]
    if new_status in valid:
        order.status = new_status
        db.session.commit()
        flash("Status atualizado.", "success")
    return redirect(url_for("admin.order_detail", order_id=order_id))


# ─── Usuários ─────────────────────────────────────────────────────────────────

@admin_bp.route("/usuarios")
@admin_required
def users():
    items = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=items)


@admin_bp.route("/usuarios/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def user_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Você não pode alterar seu próprio status de admin.", "warning")
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash("Permissão alterada.", "success")
    return redirect(url_for("admin.users"))
