from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from extensions import db
from models.user import User
from models.order import Order
from utils.auth_decorators import admin_required

user_admin = Blueprint('user_admin', __name__, url_prefix='/admin/users')


# ══════════════════════════════════════════════════════════════
# GET /admin/users  — daftar + search + filter role + pagination
# ══════════════════════════════════════════════════════════════
@user_admin.route('/')
@login_required
@admin_required
def index():
    search   = request.args.get('search', '').strip()
    role_f   = request.args.get('role', '').strip()
    page     = request.args.get('page', 1, type=int)
    per_page = 20

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.nama.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )

    if role_f in ('admin', 'user'):
        query = query.filter(User.role == role_f)

    total       = query.count()
    users       = query.order_by(User.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Hitung total order per user dalam satu query efisien
    order_counts = {}
    if users:
        uid_list = [u.id for u in users]
        rows = (
            db.session.query(Order.user_id, db.func.count(Order.id))
            .filter(Order.user_id.in_(uid_list))
            .group_by(Order.user_id)
            .all()
        )
        order_counts = {uid: cnt for uid, cnt in rows}

    counts = {
        'all':   User.query.count(),
        'admin': User.query.filter_by(role='admin').count(),
        'user':  User.query.filter_by(role='user').count(),
    }

    return render_template(
        'admin/users/index.html',
        users        = users,
        order_counts = order_counts,
        search       = search,
        role_filter  = role_f,
        counts       = counts,
        page         = page,
        total_pages  = total_pages,
        total        = total,
    )


# ══════════════════════════════════════════════════════════════
# GET /admin/users/<id>  — view detail user
# ══════════════════════════════════════════════════════════════
@user_admin.route('/<int:id>')
@login_required
@admin_required
def detail(id):
    user = User.query.get_or_404(id)

    orders = (
        Order.query
        .filter_by(user_id=user.id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    total_orders  = Order.query.filter_by(user_id=user.id).count()
    total_spent   = (
        db.session.query(db.func.sum(Order.total_harga))
        .filter(Order.user_id == user.id, Order.status == 'Completed')
        .scalar() or 0
    )

    return render_template(
        'admin/users/detail.html',
        user         = user,
        orders       = orders,
        total_orders = total_orders,
        total_spent  = total_spent,
    )


# ══════════════════════════════════════════════════════════════
# POST /admin/users/<id>/change-role
# Guard: admin tidak boleh mengubah role akun sendiri
# ══════════════════════════════════════════════════════════════
@user_admin.route('/<int:id>/change-role', methods=['POST'])
@login_required
@admin_required
def change_role(id):
    user     = User.query.get_or_404(id)
    new_role = request.form.get('role', '').strip()

    if user.id == current_user.id:
        flash('Anda tidak dapat mengubah role akun sendiri.', 'danger')
        return redirect(url_for('user_admin.index'))

    if new_role not in ('admin', 'user'):
        flash('Role tidak valid.', 'danger')
        return redirect(url_for('user_admin.index'))

    old_role  = user.role
    user.role = new_role
    db.session.commit()

    flash(
        f'Role <strong>{user.nama}</strong> diubah dari '
        f'<strong>{old_role}</strong> ke <strong>{new_role}</strong>.',
        'success'
    )
    return redirect(url_for('user_admin.index'))


# ══════════════════════════════════════════════════════════════
# POST /admin/users/<id>/delete
# Guard: admin tidak boleh menghapus akun sendiri
# ══════════════════════════════════════════════════════════════
@user_admin.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(id):
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('Anda tidak dapat menghapus akun sendiri.', 'danger')
        return redirect(url_for('user_admin.index'))

    nama = user.nama
    db.session.delete(user)
    db.session.commit()

    flash(f'User <strong>{nama}</strong> berhasil dihapus.', 'success')
    return redirect(url_for('user_admin.index'))