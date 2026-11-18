from app import app
from extensions import db
from werkzeug.security import generate_password_hash

from models.user import User
from models.category import Category
from models.product import Product


with app.app_context():

    # ==========================
    # ADMIN
    # ==========================
    existing_user = User.query.filter_by(
        username='admin'
    ).first()

    if not existing_user:

        admin = User(
            nama='Administrator',
            username='admin',
            email='admin@gmail.com',
            password=generate_password_hash('rehann123'),
            role='admin'
        )

        db.session.add(admin)

    # ==========================
    # CATEGORY
    # ==========================

    categories = [
        "Marvel",
        "DC Comics",
        "Anime",
        "Movie",
        "Game",
        "Limited Edition"
    ]

    for nama in categories:

        exists = Category.query.filter_by(
            nama_kategori=nama
        ).first()

        if not exists:
            db.session.add(
                Category(
                    nama_kategori=nama
                )
            )

    db.session.commit()

    print("Category selesai")

    # ==========================
    # PRODUCT
    # ==========================

    products = [
        {
            "nama":"Iron Man Mark 85",
            "harga":1250000,
            "stok":10,
            "gambar":"ironman.jpg",
            "kategori":"Marvel"
        },

        {
            "nama":"Spider-Man No Way Home",
            "harga":1350000,
            "stok":8,
            "gambar":"spiderman.jpg",
            "kategori":"Marvel"
        },

        {
            "nama":"Batman Dark Knight",
            "harga":1450000,
            "stok":5,
            "gambar":"batman.jpg",
            "kategori":"DC Comics"
        },

        {
            "nama":"Luffy Gear 5",
            "harga":1550000,
            "stok":7,
            "gambar":"luffy.jpg",
            "kategori":"Anime"
        }
    ]

    for item in products:

        # jangan buat dua kali
        if Product.query.filter_by(
            nama_produk=item["nama"]
        ).first():
            continue

        kategori = Category.query.filter_by(
            nama_kategori=item["kategori"]
        ).first()

        product = Product(
            nama_produk=item["nama"],
            deskripsi=f"Action Figure original {item['nama']}",
            harga=item["harga"],
            stok=item["stok"],
            gambar=item["gambar"],
            category_id=kategori.id
        )

        db.session.add(product)

    db.session.commit()

    print("Seeder selesai.")