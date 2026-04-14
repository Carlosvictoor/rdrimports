from core.extensions import db
from datetime import datetime


class Review(db.Model):
    """Avaliação geral da loja (visível na página de avaliações)."""
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)          # 1–5
    title = db.Column(db.String(120))
    body = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("reviews", lazy=True))

    def __repr__(self):
        return f"<Review #{self.id} rating={self.rating}>"


class ProductReview(db.Model):
    """Avaliação de um produto específico."""
    __tablename__ = "product_reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)          # 1–5
    title = db.Column(db.String(120))
    body = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("product_reviews", lazy=True))
    product = db.relationship(
        "Product", backref=db.backref("reviews", lazy="dynamic")
    )

    # Um usuário só avalia cada produto uma vez
    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_user_product_review"),
    )

    def __repr__(self):
        return f"<ProductReview product={self.product_id} rating={self.rating}>"
