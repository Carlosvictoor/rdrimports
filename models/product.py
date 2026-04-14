from core.extensions import db
from datetime import datetime
import re


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[àáâãä]", "a", text)
    text = re.sub(r"[èéêë]", "e", text)
    text = re.sub(r"[ìíîï]", "i", text)
    text = re.sub(r"[òóôõö]", "o", text)
    text = re.sub(r"[ùúûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float)          # para exibir desconto
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255))              # imagem principal
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    brand = db.Column(db.String(100))
    volume = db.Column(db.String(50))             # ex: "100ml"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship("OrderItem", backref="product", lazy=True)

    @staticmethod
    def make_slug(name: str) -> str:
        return _slugify(name)

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int((1 - self.price / self.original_price) * 100)
        return 0

    @property
    def image_url(self):
        if self.image:
            return f"/static/uploads/{self.image}"
        return "/static/img/no-product.png"

    def __repr__(self):
        return f"<Product {self.name}>"
