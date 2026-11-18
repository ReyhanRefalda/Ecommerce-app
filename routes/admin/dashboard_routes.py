from flask import Blueprint, render_template
from flask_login import login_required, current_user
from functools import wraps
from models.user import db, User
from models.product import Product
from models.order import Order
from models.category import Category
from sqlalchemy import extract

dashboard = Blueprint('dashboard', __name__, url_prefix='/admin')


# ── Admin-only decorator ───────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── GET /admin/dashboard ───────────────────────────────────────────────────
@dashboard.route('/dashboard')
@login_required
@admin_required
def index():
    # ── Stat cards ──
    total_products = Product.query.count()
    total_categories = Category.query.count()
    total_orders   = Order.query.count()
    total_users    = User.query.count()

    total_pendapatan  = (
        db.session.query(db.func.sum(Order.total_harga))
        .filter(Order.status == 'Completed')
        .scalar() or 0
    )

    # ── Recent orders (10 terbaru) ──
    recent_orders = (
        db.session.query(Order, User)
        .join(User, Order.user_id == User.id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    # ── Pending verification ──
    pending_verification = (
        Order.query
        .filter(Order.status == 'Waiting Verification')
        .order_by(Order.created_at.desc())
        .all()
    )
    waiting_count = len(pending_verification)

    # ── Pending payment ──
    pending_payment = (
        Order.query
        .filter(Order.status == 'Pending Payment')
        .count()
    )

    # ── Low stock (stok <= 5) ──
    low_stock = (
        Product.query
        .filter(Product.stok <= 5)
        .order_by(Product.stok.asc())
        .limit(8)
        .all()
    )

    # ── Orders per status ──
    status_counts = {
        'Pending Payment':      Order.query.filter_by(status='Pending Payment').count(),
        'Waiting Verification': Order.query.filter_by(status='Waiting Verification').count(),
        'Processing':           Order.query.filter_by(status='Processing').count(),
        'Completed':            Order.query.filter_by(status='Completed').count(),
        'Rejected':             Order.query.filter_by(status='Rejected').count(),
    }
    
    bulan_nama = [
        'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
        'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'
    ]

    label_bulan = []
    pendapatan_bulanan = []

    for bulan in range(1, 13):
        total = (
            db.session.query(db.func.sum(Order.total_harga))
            .filter(
                extract('month', Order.created_at) == bulan,
                Order.status == 'Completed'
            )
            .scalar()
        ) or 0

        label_bulan.append(bulan_nama[bulan - 1])
        pendapatan_bulanan.append(float(total))    

    return render_template(
        'admin/dashboard/index.html',
        total_products       = total_products,
        total_orders         = total_orders,
        total_users          = total_users,
        total_pendapatan     = total_pendapatan,
        recent_orders        = recent_orders,
        pending_verification = pending_verification,
        pending_payment      = pending_payment,
        low_stock            = low_stock,
        status_counts        = status_counts,
        waiting_count        = waiting_count,
        total_categories     = total_categories,
        label_bulan=label_bulan,
        pendapatan_bulanan=pendapatan_bulanan,
    )