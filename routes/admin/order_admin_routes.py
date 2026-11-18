from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from extensions import db
from models.order import Order
from models.user import User
from utils.auth_decorators import admin_required

order_admin = Blueprint('order_admin', __name__, url_prefix='/admin/orders')

ALL_STATUSES = [
    'Pending Payment',
    'Waiting Verification',
    'Processing',
    'Completed',
    'Rejected',
]

# ══════════════════════════════════════════════════════════════
# ATURAN TRANSISI STATUS (status guard)
# key   = status saat ini
# value = daftar status tujuan yang DIPERBOLEHKAN
# ══════════════════════════════════════════════════════════════
ALLOWED_TRANSITIONS = {
    'Pending Payment':      ['Waiting Verification', 'Rejected'],
    'Waiting Verification': ['Processing', 'Rejected'],
    'Processing':           ['Completed'],          # HANYA boleh maju ke Completed
    'Completed':            [],                       # tidak boleh diubah lagi
    'Rejected':              [],                       # tidak boleh diubah lagi
}


def _is_transition_allowed(current_status, new_status):
    if current_status == new_status:
        return True  # no-op, dianggap valid (tidak melanggar apapun)
    return new_status in ALLOWED_TRANSITIONS.get(current_status, [])


# ══════════════════════════════════════════════════════════════
# GET /admin/orders
# ══════════════════════════════════════════════════════════════
@order_admin.route('/')
@login_required
@admin_required
def index():
    search        = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    page          = request.args.get('page', 1, type=int)
    per_page      = 15

    query = db.session.query(Order, User).join(User, Order.user_id == User.id)

    if search:
        query = query.filter(
            db.or_(
                Order.id.like(f'%{search}%'),
                User.nama.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )

    if status_filter and status_filter in ALL_STATUSES:
        query = query.filter(Order.status == status_filter)

    query       = query.order_by(Order.created_at.desc())
    total       = query.count()
    rows        = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    status_counts = {s: Order.query.filter_by(status=s).count() for s in ALL_STATUSES}

    return render_template(
        'admin/orders/index.html',
        rows           = rows,
        search         = search,
        status_filter  = status_filter,
        all_statuses   = ALL_STATUSES,
        status_counts  = status_counts,
        page           = page,
        total_pages    = total_pages,
        total          = total,
    )


# ══════════════════════════════════════════════════════════════
# GET /admin/orders/<id>
# ══════════════════════════════════════════════════════════════
@order_admin.route('/<int:id>')
@login_required
@admin_required
def detail(id):
    order = Order.query.get_or_404(id)
    user  = User.query.get(order.user_id)

    allowed_next = ALLOWED_TRANSITIONS.get(order.status, [])

    return render_template(
        'admin/orders/detail.html',
        order        = order,
        user         = user,
        allowed_next = allowed_next,
    )


# ══════════════════════════════════════════════════════════════
# POST /admin/orders/<id>/update-status
# Dengan GUARD: hanya transisi yang diizinkan yang dieksekusi
# ══════════════════════════════════════════════════════════════
@order_admin.route('/<int:id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_status(id):
    order      = Order.query.get_or_404(id)
    new_status = request.form.get('status', '').strip()

    if new_status not in ALL_STATUSES:
        flash('Status tidak valid.', 'danger')
        return redirect(url_for('order_admin.detail', id=id))

    if not _is_transition_allowed(order.status, new_status):
        flash(
            f'Transisi status dari <strong>{order.status}</strong> ke '
            f'<strong>{new_status}</strong> tidak diperbolehkan.',
            'danger'
        )
        return redirect(url_for('order_admin.detail', id=id))

    old_status   = order.status
    order.status = new_status
    db.session.commit()

    flash(
        f'Status pesanan #{order.id:05d} diperbarui dari '
        f'<strong>{old_status}</strong> ke <strong>{new_status}</strong>.',
        'success'
    )
    return redirect(url_for('order_admin.detail', id=id))