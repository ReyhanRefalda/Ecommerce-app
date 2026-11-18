
import os
from flask import (
    Blueprint, render_template, redirect,
    url_for, request, flash, session, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models.product import Product
from models.cart import Cart
from models.order import Order
from models.order_item import OrderItem
from models.notification import Notification
from models.user import User
from utils.auth_decorators import user_required

checkout_bp = Blueprint('checkout', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class CheckoutItem:
    """Struktur item checkout seragam untuk Cart dan Buy Now."""
    def __init__(self, product, qty, cart_id=None):
        self.product = product
        self.qty     = qty
        self.cart_id = cart_id

    @property
    def subtotal(self):
        return self.product.harga * self.qty


def _resolve_checkout_items():

    source = session.get('checkout_source', 'cart')
    print("=" * 50)
    print("SOURCE =", source)
    print("BUY_NOW =", session.get('buy_now'))
    print("=" * 50)

    if source == 'buy_now' and session.get('buy_now'):
        data = session['buy_now']

        print("BUY NOW DATA =", data)

        product = Product.query.get(data['product_id'])

        if not product:
            session.pop('buy_now', None)
            session.pop('checkout_source', None)
            return [], 0, 'cart'

        item = CheckoutItem(
            product=product,
            qty=data['qty'],
            cart_id=None
        )

        print(
            f"BUY NOW ITEM => {product.nama_produk} | qty={data['qty']}"
        )

        total = item.subtotal
        return [item], total, 'buy_now'

    rows = (
        db.session.query(Cart, Product)
        .join(Product, Cart.product_id == Product.id)
        .filter(Cart.user_id == current_user.id)
        .all()
    )

    print("CART ROWS =", len(rows))

    for c, p in rows:
        print(
            f"CART => {p.nama_produk} | qty={c.qty} | cart_id={c.id}"
        )

    items = [
        CheckoutItem(
            product=p,
            qty=c.qty,
            cart_id=c.id
        )
        for c, p in rows
    ]

    total = sum(i.subtotal for i in items)

    return items, total, 'cart'




# ══════════════════════════════════════════════════════════════
# GET /checkout
# ══════════════════════════════════════════════════════════════
@checkout_bp.route('/checkout')
@login_required
@user_required
def checkout():

    items, total, source = _resolve_checkout_items()
    print("=" * 50)
    print("SESSION =", dict(session))
    print("checkout_source =", session.get('checkout_source'))
    print("buy_now =", session.get('buy_now'))
    print("=" * 50)

    for item in items:
        print(
            f"ITEM => {item.product.nama_produk} | qty={item.qty}"
        )
    if not items:
        if source == 'buy_now':
            flash('Sesi Buy Now sudah berakhir. Silakan ulangi.', 'warning')
            return redirect(url_for('user_product.products'))
        flash('Keranjang Anda kosong.', 'warning')
        return redirect(url_for('cart.index'))

    for item in items:
        if item.qty > item.product.stok:
            flash(
                f'Stok tidak mencukupi untuk '
                f'<strong>{item.product.nama_produk}</strong>.',
                'danger'
            )
            return redirect(
                url_for('user_product.products') if source == 'buy_now'
                else url_for('cart.index')
            )

    return render_template(
        'checkout/checkout.html',
        items  = items,
        total  = total,
        source = source,
    )


@checkout_bp.route('/checkout/place', methods=['POST'])
@login_required
@user_required
def place_order():
    metode = request.form.get('metode_pembayaran')
    items, _, source = _resolve_checkout_items()

    if not items:
        flash('Tidak ada produk untuk di-checkout.', 'warning')
        return redirect(url_for('user_product.products'))

    if metode not in ('QRIS', 'COD'):
        flash('Pilih metode pembayaran terlebih dahulu.', 'danger')
        return redirect(url_for('checkout.checkout'))

    for i, item in enumerate(items):
        form_qty = request.form.get(f'checkout_qty_{i}')
        if form_qty is not None:
            try:
                new_qty = int(form_qty)
                # Clamp ke [1, stok] — validasi akhir di sisi server
                if new_qty < 1:
                    new_qty = 1
                item.qty = new_qty
            except (ValueError, TypeError):
                pass  # biarkan qty lama jika konversi gagal

    total = sum(item.subtotal for item in items)


    for item in items:
        fresh = Product.query.get(item.product.id)
        if not fresh or item.qty > fresh.stok:
            sisa = fresh.stok if fresh else 0
            flash(
                f'Stok tidak mencukupi untuk '
                f'<strong>{item.product.nama_produk}</strong>. '
                f'Sisa stok: {sisa} unit.',
                'danger'
            )
            return redirect(url_for('checkout.checkout'))


    status_awal = 'Pending Payment' if metode == 'QRIS' else 'Processing'

    order = Order(
        user_id           = current_user.id,
        total_harga       = total,          # ← qty terbaru
        metode_pembayaran = metode,
        status            = status_awal,
    )
    db.session.add(order)
    db.session.flush()

    for item in items:
        order_item = OrderItem(
            order_id   = order.id,
            product_id = item.product.id,
            qty        = item.qty,
            harga      = item.product.harga,
            subtotal   = item.product.harga * item.qty
        )
        db.session.add(order_item)
     

    # Bersihkan sumber
    if source == 'buy_now':
        session.pop('buy_now', None)
    else:
        Cart.query.filter_by(user_id=current_user.id).delete()

    session.pop('checkout_source', None)

    db.session.commit()

    if metode == 'QRIS':
        return redirect(url_for('checkout.payment', order_id=order.id))
    else:
        flash('Pesanan berhasil dibuat! Kurir akan menghubungi Anda.', 'success')
        return redirect(url_for('orders.history'))



@checkout_bp.route('/checkout/payment/<int:order_id>')
@login_required
@user_required
def payment(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('checkout/payment.html', order=order)


@checkout_bp.route('/checkout/payment/<int:order_id>/upload', methods=['POST'])
@login_required
@user_required
def upload_proof(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()

    file = request.files.get('bukti_pembayaran')
    if not file or file.filename == '':
        flash('Pilih file bukti pembayaran terlebih dahulu.', 'danger')
        return redirect(url_for('checkout.payment', order_id=order_id))

    if not _allowed_file(file.filename):
        flash('Format file tidak didukung. Gunakan JPG, PNG, atau WebP.', 'danger')
        return redirect(url_for('checkout.payment', order_id=order_id))

    filename  = secure_filename(f'proof_{order.id}_{file.filename}')
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    order.bukti_pembayaran = filename
    order.status           = 'Waiting Verification'
    admins = User.query.filter_by(role='admin').all()

    for admin in admins:
        notif = Notification(
            user_id=admin.id,
            title='Pembayaran Baru',
            message=f'Pesanan #{order.id} menunggu verifikasi pembayaran.',
            link='/admin/payments'
        )

        db.session.add(notif)
    db.session.commit()

    flash('Bukti pembayaran berhasil diunggah. Menunggu verifikasi admin.', 'success')
    return redirect(url_for('order.order_history'))

