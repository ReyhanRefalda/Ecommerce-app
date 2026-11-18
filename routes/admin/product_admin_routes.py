from flask import Blueprint, render_template, request, redirect, url_for, flash

from werkzeug.utils import secure_filename

import os

from models.user import db
from models.product import Product
from models.category import Category

product = Blueprint('admin_product', __name__)

UPLOAD_FOLDER = 'static/uploads'


# Product List
@product.route('/admin/products')
def products():

    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id')
    stock_filter = request.args.get('stock_filter')
    

    query = Product.query

    # Search
    if search:
        query = query.filter(
            Product.nama_produk.ilike(f"%{search}%")
        )

    # Filter kategori
    if category_id:
        query = query.filter(
            Product.category_id == int(category_id)
        )

    # Filter stok
    if stock_filter == "ok":
        query = query.filter(Product.stok > 5)

    elif stock_filter == "low":
        query = query.filter(
            Product.stok > 0,
            Product.stok <= 5
        )

    elif stock_filter == "empty":
        query = query.filter(Product.stok == 0)

    products = query.order_by(
        Product.id.desc()
    ).all()
    total_products = Product.query.count()

    categories = Category.query.order_by(
        Category.nama_kategori.asc()
    ).all()

    return render_template(
        "admin/products/index.html",
        products=products,
        categories=categories,
        search=search,
        category_id=category_id,
        stock_filter=stock_filter,
        total_products=total_products
    )

# Create Product
@product.route('/admin/product/create', methods=['GET', 'POST'])
def create_product():

    categories = Category.query.order_by(
        Category.nama_kategori.asc()
    ).all()

    if request.method == 'POST':

        nama_produk = request.form.get(
            'nama_produk',
            ''
        ).strip()

        deskripsi = request.form.get(
            'deskripsi',
            ''
        ).strip()

        harga = request.form.get('harga')
        stok = request.form.get('stok')
        category_id = request.form.get('category_id')

        gambar = request.files.get('gambar')

        # Validasi nama produk
        if not nama_produk:
            flash(
                'Nama produk wajib diisi',
                'danger'
            )
            return redirect(request.url)

        # Validasi harga & stok
        try:
            harga = int(harga)
            stok = int(stok)
        except (ValueError, TypeError):
            flash(
                'Harga atau stok tidak valid',
                'danger'
            )
            return redirect(request.url)

        # Validasi kategori
        if category_id:

            category = Category.query.get(
                category_id
            )

            if not category:
                flash(
                    'Kategori tidak ditemukan',
                    'danger'
                )
                return redirect(request.url)

        # Upload gambar
        filename = None

        if gambar and gambar.filename:

            filename = secure_filename(
                gambar.filename
            )

            gambar.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    filename
                )
            )

        # Simpan produk
        product_data = Product(
            nama_produk=nama_produk,
            deskripsi=deskripsi,
            harga=harga,
            stok=stok,
            gambar=filename,
            category_id=int(category_id)
            if category_id else None
        )

        db.session.add(product_data)
        db.session.commit()

        flash(
            'Produk berhasil ditambahkan',
            'success'
        )

        return redirect(
            url_for('admin_product.products')
        )

    return render_template(
        'admin/products/create_product.html',
        categories=categories
    )

# Detail Product
@product.route('/admin/product/<int:id>')
def detail_product(id):

    product_data = Product.query.get_or_404(id)

    return render_template(
        'admin/products/detail_product.html',
        product=product_data
    )


# Edit Product
@product.route('/admin/product/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):

    product_data = Product.query.get_or_404(id)

    categories = Category.query.order_by(
        Category.nama_kategori.asc()
    ).all()

    error = None

    if request.method == 'POST':

        nama_produk = request.form.get('nama_produk', '').strip()
        deskripsi = request.form.get('deskripsi', '').strip()
        harga = request.form.get('harga')
        stok = request.form.get('stok')
        category_id = request.form.get('category_id')

        # Terima kedua kemungkinan nama field
        gambar = request.files.get('gambar')

        if gambar is None:
            gambar = request.files.get('image')

        print("=" * 50)
        print("FORM :", request.form)
        print("FILES :", request.files)
        print("GAMBAR :", gambar)

        try:
            harga = int(harga)
            stok = int(stok)
        except (ValueError, TypeError):

            error = "Harga atau stok tidak valid"

            return render_template(
                'admin/products/edit_product.html',
                product=product_data,
                categories=categories,
                error=error
            )

        if gambar and gambar.filename:

            filename = secure_filename(gambar.filename)

            path = os.path.join(
                UPLOAD_FOLDER,
                filename
            )

            print("SAVE :", path)

            gambar.save(path)

            print("EXIST :", os.path.exists(path))

            product_data.gambar = filename

        product_data.nama_produk = nama_produk
        product_data.deskripsi = deskripsi
        product_data.harga = harga
        product_data.stok = stok
        product_data.category_id = (
            int(category_id)
            if category_id else None
        )

        db.session.commit()

        flash(
            "Produk berhasil diupdate",
            "success"
        )

        return redirect(
            url_for("admin_product.products")
        )

    return render_template(
        "admin/products/edit_product.html",
        product=product_data,
        categories=categories,
        error=error
    )

# Delete Product
@product.route('/admin/product/delete/<int:id>', methods=['POST'])
def delete_product(id):

    product_data = Product.query.get_or_404(id)

    if product_data.gambar:
        image_path = os.path.join(UPLOAD_FOLDER, product_data.gambar)

        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(product_data)
    db.session.commit()

    flash('Produk berhasil dihapus', 'success')

    return redirect(url_for('admin_product.products'))