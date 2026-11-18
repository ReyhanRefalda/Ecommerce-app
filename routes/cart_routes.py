
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from flask_login import login_required, current_user

from models.cart import Cart
from models.product import Product
from extensions import db

from utils.auth_decorators import user_required



cart_bp = Blueprint('cart', __name__)


def _get_cart_items(user_id):
    items = (
        db.session.query(Cart, Product)
        .join(Product, Cart.product_id == Product.id)
        .filter(Cart.user_id == user_id)
        .all()
    )
    total = sum(item.Cart.qty * item.Product.harga for item in items)
    return items, total


# ── GET /cart ──────────────────────────────────────────────
@cart_bp.route('/cart')
@login_required
@user_required
def index():
    items, total = _get_cart_items(current_user.id)
    return render_template('cart/index.html', items=items, total=total)

@cart_bp.route('/cart/checkout')
@login_required
@user_required
def cart_checkout():

    session['checkout_source'] = 'cart'
    session.pop('buy_now', None)

    print("CART CHECKOUT CLICKED")
    print("SESSION =", dict(session))

    return redirect(url_for('checkout.checkout'))


# ── POST /cart/add/<id> ───────────────────────────────────
@cart_bp.route('/cart/add/<int:id>', methods=['POST'])
@login_required
@user_required
def add(id):
    product = Product.query.get_or_404(id)
    qty     = int(request.form.get('qty', 1))

    if qty < 1:
        qty = 1
    if qty > product.stok:
        flash(f'Stok {product.nama_produk} hanya tersisa {product.stok} unit.', 'danger')
        return redirect(url_for('product.detail', id=id))

    existing = Cart.query.filter_by(user_id=current_user.id, product_id=id).first()

    if existing:
        new_qty = existing.qty + qty
        if new_qty > product.stok:
            flash('Jumlah melebihi stok yang tersedia.', 'danger')
            return redirect(url_for('product.detail', id=id))
        existing.qty = new_qty
    else:
        cart_item = Cart(user_id=current_user.id, product_id=id, qty=qty)
        db.session.add(cart_item)

    db.session.commit()
    flash(f'<strong>{product.nama_produk}</strong> berhasil ditambahkan ke keranjang.', 'success')
    return redirect(url_for('cart.index'))


# ── POST /cart/update/<id> ────────────────────────────────
@cart_bp.route('/cart/update/<int:id>', methods=['POST'])
@login_required
@user_required
def update(id):
    
    print("FORM =", request.form)

    cart_item = Cart.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    

    qty = int(request.form.get('qty', 1))
    
    print("QTY RECEIVED =", qty)

    product = Product.query.get(cart_item.product_id)

    if not product:
        flash('Produk tidak ditemukan.', 'danger')
        return redirect(url_for('cart.index'))

    if qty < 1:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item dihapus dari keranjang.', 'info')
        return redirect(url_for('cart.index'))

    elif qty > product.stok:
        flash('Jumlah melebihi stok yang tersedia.', 'danger')
        return redirect(url_for('cart.index'))

    else:
        cart_item.qty = qty
        db.session.commit()
        print("DB SAVED =", cart_item.qty)
        flash('Keranjang berhasil diperbarui.', 'success')
        return redirect(url_for('cart.index'))


# ── POST /cart/remove/<id> ────────────────────────────────
@cart_bp.route('/cart/remove/<int:id>', methods=['POST'])
@login_required
@user_required
def remove(id):
    cart_item = Cart.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item berhasil dihapus dari keranjang.', 'info')
    return redirect(url_for('cart.index'))


# ── POST /cart/clear ───────────────────────────────────────
@cart_bp.route('/cart/clear', methods=['POST'])
@login_required
@user_required
def clear():
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Keranjang berhasil dikosongkan.', 'info')
    return redirect(url_for('cart.index'))