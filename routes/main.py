from flask import Blueprint, render_template, request, abort
from flask_login import current_user
from models.product import Product
from models.category import Category
from models.review import ProductReview
from models.order import Order, OrderItem
from sqlalchemy import or_, func
from core.security import sanitize_search

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    featured = Product.query.filter_by(featured=True, active=True).limit(8).all()
    categories = Category.query.all()
    return render_template("index.html", featured=featured, categories=categories)


@main_bp.route("/loja")
def catalog():
    from flask import current_app
    page = request.args.get("page", 1, type=int)
    q = sanitize_search(request.args.get("q", ""))
    category_slug = request.args.get("categoria", "")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)

    query = Product.query.filter_by(active=True)

    if q:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%"),
                Product.brand.ilike(f"%{q}%"),
            )
        )
    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    categories = Category.query.all()
    return render_template(
        "shop/catalog.html",
        products=products,
        categories=categories,
        q=q,
        active_category=category_slug,
    )


@main_bp.route("/produto/<slug>")
def product_detail(slug):
    from core.extensions import db
    product = Product.query.filter_by(slug=slug, active=True).first_or_404()
    related = (
        Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.active == True,
        )
        .limit(4)
        .all()
    )

    # Avaliações e média do produto
    product_reviews = (
        ProductReview.query
        .filter_by(product_id=product.id, approved=True)
        .order_by(ProductReview.created_at.desc())
        .all()
    )
    avg_rating = (
        db.session.query(func.avg(ProductReview.rating))
        .filter_by(product_id=product.id, approved=True)
        .scalar() or 0
    )

    # Verifica se usuário pode avaliar (comprou e ainda não avaliou)
    can_review = False
    user_product_review = None
    if current_user.is_authenticated:
        user_product_review = ProductReview.query.filter_by(
            user_id=current_user.id, product_id=product.id
        ).first()
        if not user_product_review:
            can_review = db.session.query(
                db.exists().where(
                    OrderItem.product_id == product.id,
                    OrderItem.order_id == Order.id,
                    Order.user_id == current_user.id,
                    Order.status.in_(["pago", "enviado", "entregue"]),
                )
            ).scalar()

    return render_template(
        "shop/product.html",
        product=product,
        related=related,
        product_reviews=product_reviews,
        avg_rating=avg_rating,
        can_review=can_review,
        user_product_review=user_product_review,
    )
