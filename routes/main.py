from flask import Blueprint, render_template, request, abort
from models.product import Product
from models.category import Category
from sqlalchemy import or_

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
    q = request.args.get("q", "").strip()
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
    return render_template("shop/product.html", product=product, related=related)
