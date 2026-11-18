from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from extensions import db
from models.product import Product
from models.category import Category

product_bp = Blueprint('user_product', __name__)


# ══════════════════════════════════════════════════════════════
# GET /products  — daftar produk (TIDAK diubah, hanya disertakan
# agar konteks lengkap untuk template index.html)
# ══════════════════════════════════════════════════════════════
@product_bp.route('/products')
def products():
    search   = request.args.get('search', '').strip()
    sort     = request.args.get('sort', 'terbaru')
    cat_id   = request.args.get('category_id', '', type=str).strip()
    page     = request.args.get('page', 1, type=int)
    per_page = 12

    query = Product.query

    if search:
        query = query.filter(Product.nama_produk.ilike(f'%{search}%'))
    if cat_id:
        query = query.filter(Product.category_id == cat_id)

    if sort == 'harga_asc':
        query = query.order_by(Product.harga.asc())
    elif sort == 'harga_desc':
        query = query.order_by(Product.harga.desc())
    elif sort == 'nama_az':
        query = query.order_by(Product.nama_produk.asc())
    else:
        query = query.order_by(Product.id.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products   = pagination.items
    categories = Category.query.order_by(Category.nama_kategori).all()

    return render_template(
        'products/index.html',
        products   = products,
        pagination = pagination,
        search     = search,
        sort       = sort,
        cat_id     = cat_id,
        categories = categories,
    )


# ══════════════════════════════════════════════════════════════
# GET /product/<id>  — detail produk (TIDAK diubah)
# ══════════════════════════════════════════════════════════════
@product_bp.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    related = (
        Product.query
        .filter(Product.id != id, Product.stok > 0)
        .order_by(Product.id.desc())
        .limit(4)
        .all()
    )
    return render_template('products/detail.html', product=product, related=related)


# ══════════════════════════════════════════════════════════════
# POST /buy-now/<id>  — Buy Now
#
# PENTING (Order Consistency — Part 4):
# Route ini HANYA menyimpan product_id + qty ke session.
# TIDAK menyentuh stok produk sama sekali. Stok baru dikurangi
# nanti di route checkout.place_order, HANYA setelah order
# benar-benar berhasil dibuat dan disimpan ke database.
# ══════════════════════════════════════════════════════════════
@product_bp.route('/buy-now/<int:id>', methods=['POST'])
@login_required
def buy_now(id):

    print("FORM =", request.form)

    product = Product.query.get_or_404(id)

    qty = int(request.form.get('qty', 1))

    print("QTY =", qty)

    # ── Validasi stok SAAT INI (hanya pengecekan, bukan pengurangan) ──
    if product.stok == 0:
        flash(f'<strong>{product.nama_produk}</strong> sedang habis.', 'danger')
        return redirect(url_for('product.detail', id=id))

    if qty > product.stok:
        flash(
            f'Stok produk tidak mencukupi. '
            f'<strong>{product.nama_produk}</strong> hanya tersisa {product.stok} unit.',
            'danger'
        )
        return redirect(url_for('product.detail', id=id))

    # ── Simpan sumber checkout = 'buy_now' di session ─────────
    # Cart TIDAK tersentuh sama sekali.
    session['checkout_source'] = 'buy_now'
    session['buy_now'] = {
        'product_id': product.id,
        'qty':        qty,
    }

    return redirect(url_for('checkout.checkout'))