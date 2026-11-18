from extensions import db
from models.category import Category

def run():
    categories = [
        "Marvel",
        "DC Comics",
        "Anime",
        "Manga",
        "Movie",
        "Game",
        "Collectible",
        "Limited Edition"
    ]

    for nama in categories:
        exists = Category.query.filter_by(
            nama_kategori=nama
        ).first()

        if not exists:
            db.session.add(
                Category(nama_kategori=nama)
            )

    db.session.commit()

    print("✅ Category Seeder berhasil dijalankan")