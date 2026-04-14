from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from core.extensions import db
from models.order import Order, OrderItem
from models.product import Product
from routes.cart import _get_cart, _save_cart, cart_total
import mercadopago

payment_bp = Blueprint("payment", __name__)


@payment_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = _get_cart()
    if not cart:
        flash("Seu carrinho está vazio.", "warning")
        return redirect(url_for("cart.view"))

    if request.method == "POST":
        # Salva pedido
        total = cart_total(cart)
        order = Order(
            user_id=current_user.id,
            total=total,
            address_zip=request.form.get("zip", "").strip(),
            address_street=request.form.get("street", "").strip(),
            address_number=request.form.get("number", "").strip(),
            address_complement=request.form.get("complement", "").strip(),
            address_city=request.form.get("city", "").strip(),
            address_state=request.form.get("state", "").strip().upper(),
        )
        db.session.add(order)
        db.session.flush()  # gera o id antes de commitar

        for pid, item in cart.items():
            product = Product.query.get(int(pid))
            if product and product.stock >= item["qty"]:
                oi = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=item["qty"],
                    unit_price=item["price"],
                )
                product.stock -= item["qty"]
                db.session.add(oi)

        db.session.commit()

        # Cria preferência no Mercado Pago
        mp_preference_id = _create_mp_preference(order, cart)
        if mp_preference_id:
            order.mp_preference_id = mp_preference_id
            db.session.commit()
            _save_cart({})
            return redirect(url_for("payment.mp_redirect", order_id=order.id))

        # Fallback: sem MP configurado
        _save_cart({})
        flash("Pedido criado! Aguardando pagamento.", "success")
        return redirect(url_for("payment.success", order_id=order.id))

    total = cart_total(cart)
    return render_template("checkout/checkout.html", cart=cart, total=total)


def _create_mp_preference(order: Order, cart: dict):
    access_token = current_app.config.get("MP_ACCESS_TOKEN", "")
    if not access_token or access_token == "SEU_ACCESS_TOKEN_AQUI":
        return None

    sdk = mercadopago.SDK(access_token)
    base_url = current_app.config["BASE_URL"]

    items = []
    for pid, item in cart.items():
        items.append({
            "title": item["name"],
            "quantity": item["qty"],
            "unit_price": float(item["price"]),
            "currency_id": "BRL",
        })

    preference_data = {
        "items": items,
        "payer": {
            "email": order.user.email,
            "name": order.user.name,
        },
        "back_urls": {
            "success": f"{base_url}/pagamento/sucesso/{order.id}",
            "failure": f"{base_url}/pagamento/falha/{order.id}",
            "pending": f"{base_url}/pagamento/pendente/{order.id}",
        },
        "auto_return": "approved",
        "external_reference": str(order.id),
        "notification_url": f"{base_url}/pagamento/webhook",
    }

    result = sdk.preference().create(preference_data)
    response = result.get("response", {})
    return response.get("id")


@payment_bp.route("/redirecionar/<int:order_id>")
@login_required
def mp_redirect(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash("Acesso negado.", "danger")
        return redirect(url_for("main.index"))

    mp_access_token = current_app.config.get("MP_ACCESS_TOKEN", "")
    sdk = mercadopago.SDK(mp_access_token)
    pref = sdk.preference().get(order.mp_preference_id)
    init_point = pref.get("response", {}).get("init_point", url_for("main.index"))
    return redirect(init_point)


@payment_bp.route("/sucesso/<int:order_id>")
@login_required
def success(order_id):
    order = Order.query.get_or_404(order_id)
    payment_id = request.args.get("payment_id")
    status = request.args.get("status", "")

    if payment_id:
        order.mp_payment_id = payment_id
        order.mp_status = status
        if status == "approved":
            order.status = Order.STATUS_PAID
        db.session.commit()

    return render_template("checkout/success.html", order=order)


@payment_bp.route("/falha/<int:order_id>")
@login_required
def failure(order_id):
    order = Order.query.get_or_404(order_id)
    flash("Pagamento não aprovado. Tente novamente.", "danger")
    return redirect(url_for("payment.checkout"))


@payment_bp.route("/pendente/<int:order_id>")
@login_required
def pending(order_id):
    order = Order.query.get_or_404(order_id)
    flash("Pagamento pendente. Avisaremos quando for confirmado.", "warning")
    return render_template("checkout/success.html", order=order)


@payment_bp.route("/webhook", methods=["POST"])
def webhook():
    """Webhook do Mercado Pago para notificações de pagamento."""
    data = request.get_json(silent=True) or {}
    topic = data.get("type") or request.args.get("topic", "")

    if topic == "payment":
        payment_id = data.get("data", {}).get("id") or request.args.get("id")
        if payment_id:
            mp_access_token = current_app.config.get("MP_ACCESS_TOKEN", "")
            if mp_access_token:
                sdk = mercadopago.SDK(mp_access_token)
                result = sdk.payment().get(payment_id)
                payment = result.get("response", {})
                order_id = payment.get("external_reference")
                status = payment.get("status", "")
                if order_id:
                    order = Order.query.get(int(order_id))
                    if order:
                        order.mp_payment_id = str(payment_id)
                        order.mp_status = status
                        if status == "approved":
                            order.status = Order.STATUS_PAID
                        from core.extensions import db as _db
                        _db.session.commit()
    return "", 200
