from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models.category import Category
from models.product import Product

# ── Blueprint ──────────────────────────────────────────────────────────────
category_admin = Blueprint('category_admin', __name__, url_prefix='/admin/categories')


# ── Admin-only guard ───────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════════════════
# GET  /admin/categories          ── daftar kategori
# ══════════════════════════════════════════════════════════════════════════════
@category_admin.route('/')
@login_required
@admin_required
def index():
    search = request.args.get('search', '').strip()

    query = Category.query

    if search:
        query = query.filter(
            Category.nama_kategori.ilike(f'%{search}%')
        )

    categories = query.order_by(Category.id.asc()).all()

    # Hitung jumlah produk per kategori
    product_counts = {}
    for cat in categories:
        product_counts[cat.id] = Product.query.filter_by(category_id=cat.id).count()

    return render_template(
        'admin/category/index.html',
        categories     = categories,
        product_counts = product_counts,
        search         = search,
        total          = len(categories),
    )


# ══════════════════════════════════════════════════════════════════════════════
# GET + POST  /admin/categories/create   ── tambah kategori
# ══════════════════════════════════════════════════════════════════════════════
@category_admin.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    if request.method == 'POST':
        nama = request.form.get('nama_kategori', '').strip()

        # ── Validasi: tidak boleh kosong ──
        if not nama:
            flash('Nama kategori tidak boleh kosong.', 'danger')
            return render_template('admin/category/create.html', nama=nama)

        # ── Validasi: harus unik ──
        existing = Category.query.filter(
            db.func.lower(Category.nama_kategori) == nama.lower()
        ).first()

        if existing:
            flash(
                f'Kategori {nama} sudah ada. Gunakan nama yang berbeda.',
                'danger'
            )
            return render_template('admin/category/create.html', nama=nama)

        # ── Simpan ──
        new_cat = Category(nama_kategori=nama)
        db.session.add(new_cat)
        db.session.commit()

        flash(
            f'Kategori {nama} berhasil ditambahkan.',
            'success'
        )
        return redirect(url_for('category_admin.index'))

    return render_template('admin/category/create.html', nama='')


# ══════════════════════════════════════════════════════════════════════════════
# GET + POST  /admin/categories/edit/<id>   ── edit kategori
# ══════════════════════════════════════════════════════════════════════════════
@category_admin.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    category = Category.query.get_or_404(id)

    if request.method == 'POST':
        nama = request.form.get('nama_kategori', '').strip()

        # ── Validasi: tidak boleh kosong ──
        if not nama:
            flash('Nama kategori tidak boleh kosong.', 'danger')
            return render_template('admin/category/edit.html', category=category, nama=nama)

        # ── Validasi: unik, kecuali kategori itu sendiri ──
        existing = Category.query.filter(
            db.func.lower(Category.nama_kategori) == nama.lower(),
            Category.id != id
        ).first()

        if existing:
            flash(
                f'Kategori {nama} sudah ada. Gunakan nama yang berbeda.',
                'danger'
            )
            return render_template('admin/category/edit.html', category=category, nama=nama)

        # ── Update ──
        old_name          = category.nama_kategori
        category.nama_kategori = nama
        db.session.commit()

        flash(
            f'Kategori {old_name} berhasil diubah menjadi {nama}.',
            'success'
        )
        return redirect(url_for('category_admin.index'))

    return render_template(
        'admin/category/edit.html',
        category = category,
        nama     = category.nama_kategori,
    )


# ══════════════════════════════════════════════════════════════════════════════
# POST  /admin/categories/delete/<id>   ── hapus kategori
# ══════════════════════════════════════════════════════════════════════════════
@category_admin.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete(id):
    category = Category.query.get_or_404(id)

    # ── Cek apakah masih dipakai produk ──
    product_count = Product.query.filter_by(category_id=id).count()

    if product_count > 0:
        flash(
            f'Kategori {category.nama_kategori} tidak dapat dihapus '
            f'karena masih digunakan oleh {product_count} produk. '
            f'Pindahkan atau hapus produk terlebih dahulu.',
            'danger'
        )
        return redirect(url_for('category_admin.index'))

    nama = category.nama_kategori
    db.session.delete(category)
    db.session.commit()

    flash(
        f'Kategori {nama} berhasil dihapus.',
        'success'
    )
    return redirect(url_for('category_admin.index'))