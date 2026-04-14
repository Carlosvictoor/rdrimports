from core.extensions import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = "orders"

    STATUS_PENDING = "pendente"
    STATUS_PAID = "pago"
    STATUS_SHIPPED = "enviado"
    STATUS_DELIVERED = "entregue"
    STATUS_CANCELLED = "cancelado"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default=STATUS_PENDING)
    total = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Endereço de entrega
    address_zip = db.Column(db.String(10))
    address_street = db.Column(db.String(200))
    address_number = db.Column(db.String(20))
    address_complement = db.Column(db.String(100))
    address_city = db.Column(db.String(100))
    address_state = db.Column(db.String(2))

    # Mercado Pago
    mp_preference_id = db.Column(db.String(100))
    mp_payment_id = db.Column(db.String(100))
    mp_status = db.Column(db.String(50))

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    @property
    def status_label(self):
        labels = {
            "pendente": ("Pendente", "warning"),
            "pago": ("Pago", "success"),
            "enviado": ("Enviado", "info"),
            "entregue": ("Entregue", "success"),
            "cancelado": ("Cancelado", "danger"),
        }
        return labels.get(self.status, (self.status, "secondary"))

    def __repr__(self):
        return f"<Order #{self.id}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
