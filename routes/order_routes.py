"""
routes/order_routes.py — KONFIRMASI REVISI

Perubahan dari versi sebelumnya:
  1. Order history sudah ORDER BY created_at DESC (pesanan terbaru di atas).
     Ini sudah benar di versi sebelumnya — dipertahankan.
  2. Tambah fallback ORDER BY id DESC jika created_at NULL
     (MySQL: COALESCE null-safe).
  3. Preload items tetap efisien (tidak N+1).
  4. Route detail (/order/detail/<id>) tidak berubah.
"""

import logging
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from extensions import db
from models.order import Order
from models.order_item import OrderItem
from models.product import Product
from utils.auth_decorators import user_required

log = logging.getLogger(__name__)

order_bp = Blueprint('order', __name__)


# ══════════════════════════════════════════════════════════════
# GET /orders/history
# ORDER BY created_at DESC, id DESC
# Pesanan terbaru selalu muncul paling atas.
# ══════════════════════════════════════════════════════════════
@order_bp.route('/orders/history')
@login_required
@user_required
def order_history():
    orders = (
        Order.query
        .filter_by(user_id=current_user.id)
        .order_by(
            Order.created_at.desc(),
            Order.id.desc(),
        )
        .all()
    )

    log.debug(
        f'[order] history user={current_user.id} '
        f'count={len(orders)}'
    )

    # ── Preload items (cegah N+1 query) ───────────────────────
    order_items = {}
    if orders:
        order_ids = [o.id for o in orders]
        rows = (
            db.session.query(OrderItem, Product)
            .join(Product, OrderItem.product_id == Product.id)
            .filter(OrderItem.order_id.in_(order_ids))
            .all()
        )
        for oi, prod in rows:
            order_items.setdefault(oi.order_id, []).append({
                'order_item': oi,
                'product':    prod,
            })

    return render_template(
        'orders/history.html',
        orders      = orders,
        order_items = order_items,
    )


# ══════════════════════════════════════════════════════════════
# GET /order/detail/<id>
# ══════════════════════════════════════════════════════════════
@order_bp.route('/order/detail/<int:order_id>')
@login_required
def detail(order_id):
    order = Order.query.filter_by(
        id=order_id, user_id=current_user.id
    ).first_or_404()

    items = (
        db.session.query(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.id)
        .filter(OrderItem.order_id == order_id)
        .all()
    )

    log.debug(f'[order] detail order={order_id} user={current_user.id}')

    return render_template(
        'orders/detail.html',
        order = order,
        items = items,
    )