import random

from extensions import db
from models.product import Product
from models.category import Category


def run():

    if Product.query.count() > 0:
        print("Produk sudah ada.")
        return

    data = [

        {
            "nama": "Iron Man Mark 85",
            "harga": 1250000,
            "stok": 12,
            "gambar": "ironman.jpg",
            "kategori": "Marvel"
        },

        {
            "nama": "Captain America Endgame",
            "harga": 1180000,
            "stok": 8,
            "gambar": "captain.jpg",
            "kategori": "Marvel"
        },

        {
            "nama": "Spider-Man No Way Home",
            "harga": 1350000,
            "stok": 10,
            "gambar": "spiderman.jpg",
            "kategori": "Marvel"
        },

        {
            "nama": "Batman Dark Knight",
            "harga": 1450000,
            "stok": 7,
            "gambar": "batman.jpg",
            "kategori": "DC Comics"
        },

        {
            "nama": "Superman Justice League",
            "harga": 1320000,
            "stok": 5,
            "gambar": "superman.jpg",
            "kategori": "DC Comics"
        },

        {
            "nama": "Joker DX Version",
            "harga": 1680000,
            "stok": 4,
            "gambar": "joker.jpg",
            "kategori": "DC Comics"
        },

        {
            "nama": "Monkey D Luffy Gear 5",
            "harga": 1650000,
            "stok": 9,
            "gambar": "luffy.jpg",
            "kategori": "Anime"
        },

        {
            "nama": "Roronoa Zoro",
            "harga": 1320000,
            "stok": 11,
            "gambar": "zoro.jpg",
            "kategori": "Anime"
        },

        {
            "nama": "Naruto Sage Mode",
            "harga": 980000,
            "stok": 13,
            "gambar": "naruto.jpg",
            "kategori": "Anime"
        },

        {
            "nama": "Sasuke Uchiha",
            "harga": 990000,
            "stok": 9,
            "gambar": "sasuke.jpg",
            "kategori": "Anime"
        },

        {
            "nama": "Gojo Satoru",
            "harga": 1100000,
            "stok": 10,
            "gambar": "gojo.jpg",
            "kategori": "Anime"
        },

        {
            "nama": "Yuji Itadori",
            "harga": 875000,
            "stok": 14,
            "gambar": "yuji.jpg",
            "kategori": "Anime"
        },

        {
            "nama": "Goku Ultra Instinct",
            "harga": 1400000,
            "stok": 8,
            "gambar": "goku.jpg",
            "kategori": "Anime"
        },

        {
            "nama": "Vegeta Blue",
            "harga": 1200000,
            "stok": 6,
            "gambar": "vegeta.jpg",
            "kategori": "Anime"
        },

        {
            "nama": "Leon Kennedy RE4",
            "harga": 1550000,
            "stok": 4,
            "gambar": "leon.jpg",
            "kategori": "Game"
        },

        {
            "nama": "Kratos Ragnarok",
            "harga": 1850000,
            "stok": 5,
            "gambar": "kratos.jpg",
            "kategori": "Game"
        }

    ]

    for item in data:

        category = Category.query.filter_by(
            nama_kategori=item["kategori"]
        ).first()

        produk = Product(
            nama_produk=item["nama"],
            deskripsi=f"Action Figure original {item['nama']} dengan kualitas premium.",
            harga=item["harga"],
            stok=item["stok"],
            gambar=item["gambar"],
            category_id=category.id
        )

        db.session.add(produk)

    db.session.commit()

    print("✅ Product Seeder berhasil dijalankan")