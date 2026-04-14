from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from core.extensions import db, limiter
from core.security import sanitize_text
from models.review import Review, ProductReview
from models.product import Product
from models.order import Order, OrderItem
from sqlalchemy import func

reviews_bp = Blueprint("reviews", __name__)


def _user_bought_product(user_id: int, product_id: int) -> bool:
    """Verifica se o usuário comprou o produto (pedido pago ou entregue)."""
    return db.session.query(
        db.exists().where(
            OrderItem.product_id == product_id,
            OrderItem.order_id == Order.id,
            Order.user_id == user_id,
            Order.status.in_(["pago", "enviado", "entregue"]),
        )
    ).scalar()


# ─── Página pública de avaliações da loja ────────────────────────────────────

@reviews_bp.route("/avaliacoes")
def index():
    page = request.args.get("page", 1, type=int)
    reviews = (
        Review.query.filter_by(approved=True)
        .order_by(Review.created_at.desc())
        .paginate(page=page, per_page=12, error_out=False)
    )
    # Estatísticas globais
    stats = db.session.query(
        func.count(Review.id).label("total"),
        func.avg(Review.rating).label("avg_rating"),
        func.sum(db.case((Review.rating == 5, 1), else_=0)).label("r5"),
        func.sum(db.case((Review.rating == 4, 1), else_=0)).label("r4"),
        func.sum(db.case((Review.rating == 3, 1), else_=0)).label("r3"),
        func.sum(db.case((Review.rating == 2, 1), else_=0)).label("r2"),
        func.sum(db.case((Review.rating == 1, 1), else_=0)).label("r1"),
    ).first()

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(user_id=current_user.id).first()

    return render_template(
        "reviews/index.html",
        reviews=reviews,
        stats=stats,
        user_review=user_review,
    )


# ─── Criar avaliação da loja ─────────────────────────────────────────────────

@reviews_bp.route("/avaliacoes/nova", methods=["GET", "POST"])
@login_required
@limiter.limit("3 per hour")
def create():
    if Review.query.filter_by(user_id=current_user.id).first():
        flash("Você já avaliou a loja.", "info")
        return redirect(url_for("reviews.index"))

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        title = sanitize_text(request.form.get("title", ""), max_len=120)
        body = sanitize_text(request.form.get("body", ""), max_len=1000)

        if not rating or not (1 <= rating <= 5):
            flash("Selecione uma nota de 1 a 5 estrelas.", "danger")
            return render_template("reviews/form.html", mode="store")
        if not body or len(body.strip()) < 10:
            flash("Escreva um comentário com pelo menos 10 caracteres.", "danger")
            return render_template("reviews/form.html", mode="store")

        review = Review(
            user_id=current_user.id,
            rating=rating,
            title=title,
            body=body.strip(),
        )
        db.session.add(review)
        db.session.commit()
        flash("Obrigado pela sua avaliação!", "success")
        return redirect(url_for("reviews.index"))

    return render_template("reviews/form.html", mode="store")


# ─── Criar avaliação de produto ───────────────────────────────────────────────

@reviews_bp.route("/produto/<int:product_id>/avaliar", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per hour")
def create_product(product_id):
    product = Product.query.get_or_404(product_id)

    if ProductReview.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first():
        flash("Você já avaliou este produto.", "info")
        return redirect(url_for("main.product_detail", slug=product.slug))

    if not _user_bought_product(current_user.id, product_id):
        flash("Você só pode avaliar produtos que comprou.", "warning")
        return redirect(url_for("main.product_detail", slug=product.slug))

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        title = sanitize_text(request.form.get("title", ""), max_len=120)
        body = sanitize_text(request.form.get("body", ""), max_len=1000)

        if not rating or not (1 <= rating <= 5):
            flash("Selecione uma nota de 1 a 5 estrelas.", "danger")
            return render_template("reviews/form.html", mode="product", product=product)
        if not body or len(body.strip()) < 10:
            flash("Escreva um comentário com pelo menos 10 caracteres.", "danger")
            return render_template("reviews/form.html", mode="product", product=product)

        review = ProductReview(
            user_id=current_user.id,
            product_id=product_id,
            rating=rating,
            title=title,
            body=body.strip(),
        )
        db.session.add(review)
        db.session.commit()
        flash("Avaliação publicada! Obrigado.", "success")
        return redirect(url_for("main.product_detail", slug=product.slug))

    return render_template("reviews/form.html", mode="product", product=product)


# ─── Deletar avaliação própria ────────────────────────────────────────────────

@reviews_bp.route("/avaliacoes/<int:review_id>/excluir", methods=["POST"])
@login_required
def delete(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(review)
    db.session.commit()
    flash("Avaliação removida.", "info")
    return redirect(url_for("reviews.index"))
