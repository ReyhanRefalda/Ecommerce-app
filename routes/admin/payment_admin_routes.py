from flask import Blueprint, logging, render_template, redirect, url_for, request, flash
from flask_login import login_required
from extensions import db
from models import order
from models.order import Order
from models.order_item import OrderItem
from models.product import Product
from models.user import User
from utils.auth_decorators import admin_required
from models.notification import Notification
from flask import url_for
from utils.notification_helper import notify_order_status
 


payment_admin = Blueprint('payment_admin', __name__, url_prefix='/admin/payments')


# ══════════════════════════════════════════════════════════════
# GET /admin/payments
# Hanya menampilkan: metode_pembayaran = QRIS DAN status = Waiting Verification
# ══════════════════════════════════════════════════════════════
@payment_admin.route('/')
@login_required
@admin_required
def index():
    search   = request.args.get('search', '').strip()
    page     = request.args.get('page', 1, type=int)
    per_page = 15

    query = (
        db.session.query(Order, User)
        .join(User, Order.user_id == User.id)
        .filter(
            Order.metode_pembayaran == 'QRIS',
            Order.status == 'Waiting Verification',
        )
    )

    if search:
        query = query.filter(
            db.or_(
                Order.id.like(f'%{search}%'),
                User.nama.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )

    query       = query.order_by(Order.created_at.asc())   # FIFO — antrian terlama dulu
    total       = query.count()
    rows        = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        'admin/payments/index.html',
        rows        = rows,
        search      = search,
        page        = page,
        total_pages = total_pages,
        total       = total,
    )


# ══════════════════════════════════════════════════════════════
# GET /admin/payments/<id>  — detail untuk verifikasi
# ══════════════════════════════════════════════════════════════
@payment_admin.route('/<int:id>')
@login_required
@admin_required
def detail(id):
    order = Order.query.filter_by(
        id                = id,
        metode_pembayaran = 'QRIS',
    ).first_or_404()

    user = User.query.get(order.user_id)

    return render_template('admin/payments/detail.html', order=order, user=user)


# ══════════════════════════════════════════════════════════════
# POST /admin/payments/<id>/approve
# status -> Processing, otomatis hilang dari daftar Payments
# ══════════════════════════════════════════════════════════════
@payment_admin.route('/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve(id):
    order = Order.query.get_or_404(id)

    if order.status != 'Waiting Verification':
        flash('Pembayaran ini sudah diproses sebelumnya.', 'warning')
        return redirect(url_for('payment_admin.index'))

    items = OrderItem.query.filter_by(order_id=order.id).all()

        # Validasi stok
    items = OrderItem.query.filter_by(
        order_id=order.id
    ).all()

    for item in items:

        product = Product.query.get(item.product_id)

        if not product:
            flash('Produk tidak ditemukan.', 'danger')
            return redirect(
                url_for('payment_admin.detail', id=id)
            )

        if product.stok < item.qty:
            flash(
                f'Stok {product.nama_produk} tidak mencukupi.',
                'danger'
            )
            return redirect(
                url_for('payment_admin.detail', id=id)
            )

    for item in items:
        product = Product.query.get(item.product_id)
        product.stok -= item.qty

    order.status = 'Processing'


    notif = Notification(
        user_id=order.user_id,
        title='Pembayaran Diterima',
        message=f'Pesanan #{order.id:05d} berhasil diverifikasi dan sedang diproses paket akan segera dikirim.',
        link=url_for('order.order_history')
    )
    

    db.session.add(notif)
    

    db.session.commit()

    flash('Pembayaran berhasil diverifikasi. Pesanan masuk ke tahap Processing.',
    'success')
    return redirect(url_for('payment_admin.index'))


# ══════════════════════════════════════════════════════════════
# POST /admin/payments/<id>/reject
# status -> Rejected
# ══════════════════════════════════════════════════════════════
@payment_admin.route('/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def reject(id):
    order = Order.query.get_or_404(id)

    if order.status != 'Waiting Verification':
        flash('Pembayaran ini sudah diproses sebelumnya.', 'warning')
        return redirect(url_for('payment_admin.index'))

    order.status = 'Rejected'
    notif = Notification(
    user_id=order.user_id,
    title='Pembayaran Ditolak',
    message=f'Pembayaran untuk pesanan #{order.id:05d} ditolak. Silakan upload ulang bukti pembayaran.',
    link=f'/checkout/payment/{order.id}'
)

    db.session.add(notif)
    db.session.commit()

    flash(
        f'Pembayaran order <strong>#{order.id:05d}</strong> ditolak.',
        'danger'
    )
    return redirect(url_for('payment_admin.index'))
@payment_admin.route('/<int:id>/complete', methods=['POST'])
@login_required
@admin_required
def complete(id):
    order = Order.query.get_or_404(id)
 
    # ── Guard: hanya boleh dari status Processing ──────────────
    if order.status != 'Processing':
        flash(
            f'Pesanan tidak dapat diselesaikan dari status '
            f'<strong>{order.status}</strong>. '
            f'Hanya pesanan berstatus Processing yang dapat diselesaikan.',
            'warning'
        )
        return redirect(url_for('order_admin.detail', id=id))
 
    order.status = 'Completed'
    notify_order_status(order)      # ← notifikasi "Pesanan Selesai"
    db.session.commit()
 
    log.info(f'[payment_admin] complete order={id} → Completed')
    flash(
        f'Pesanan <strong>#{order.id:05d}</strong> telah diselesaikan. '
        f'User akan mendapatkan notifikasi otomatis.',
        'success'
    )
    return redirect(url_for('order_admin.detail', id=id))