from flask import Blueprint, session, redirect, url_for, request, render_template, flash, jsonify
from models.product import Product

cart_bp = Blueprint("cart", __name__)

CART_KEY = "cart"


def _get_cart() -> dict:
    return session.get(CART_KEY, {})


def _save_cart(cart: dict):
    session[CART_KEY] = cart
    session.modified = True


def cart_total(cart: dict) -> float:
    total = 0.0
    for pid, item in cart.items():
        total += item["price"] * item["qty"]
    return total


def cart_count(cart: dict) -> int:
    return sum(item["qty"] for item in cart.values())


@cart_bp.route("/adicionar/<int:product_id>", methods=["POST"])
def add(product_id):
    product = Product.query.get_or_404(product_id)
    qty = int(request.form.get("qty", 1))
    qty = max(1, min(qty, product.stock))

    cart = _get_cart()
    key = str(product_id)
    if key in cart:
        cart[key]["qty"] = min(cart[key]["qty"] + qty, product.stock)
    else:
        cart[key] = {
            "name": product.name,
            "price": product.price,
            "image": product.image_url,
            "qty": qty,
            "slug": product.slug,
        }
    _save_cart(cart)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"count": cart_count(cart), "ok": True})

    flash(f'"{product.name}" adicionado ao carrinho.', "success")
    return redirect(request.referrer or url_for("cart.view"))


@cart_bp.route("/")
def view():
    cart = _get_cart()
    total = cart_total(cart)
    return render_template("shop/cart.html", cart=cart, total=total)


@cart_bp.route("/remover/<int:product_id>", methods=["POST"])
def remove(product_id):
    cart = _get_cart()
    cart.pop(str(product_id), None)
    _save_cart(cart)
    flash("Item removido do carrinho.", "info")
    return redirect(url_for("cart.view"))


@cart_bp.route("/atualizar/<int:product_id>", methods=["POST"])
def update(product_id):
    product = Product.query.get_or_404(product_id)
    qty = int(request.form.get("qty", 1))
    cart = _get_cart()
    key = str(product_id)
    if qty <= 0:
        cart.pop(key, None)
    else:
        qty = min(qty, product.stock)
        if key in cart:
            cart[key]["qty"] = qty
    _save_cart(cart)
    return redirect(url_for("cart.view"))


@cart_bp.route("/limpar", methods=["POST"])
def clear():
    _save_cart({})
    return redirect(url_for("cart.view"))
