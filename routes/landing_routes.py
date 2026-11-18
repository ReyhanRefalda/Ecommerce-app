from flask import Blueprint, render_template
from models.product import Product
from models.category import Category

landing = Blueprint('landing', __name__)


@landing.route('/')
def index():
    # ── Featured / hero products (newest 8, in stock) ──
    products = (
        Product.query
        .filter(Product.stok > 0)
        .order_by(Product.id.desc())
        .limit(8)
        .all()
    )

    # ── Best products (stok paling banyak = paling laris, 4 items) ──
    best_products = (
        Product.query
        .filter(Product.stok > 0)
        .order_by(Product.stok.desc())
        .limit(4)
        .all()
    )

    # ── All categories with product count ──
    categories = Category.query.order_by(Category.id.asc()).all()

    return render_template(
        'landing/index.html',
        products      = products,
        best_products = best_products,
        categories    = categories,
    )