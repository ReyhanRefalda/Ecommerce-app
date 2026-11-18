from extensions import db

class Product(db.Model):

    __tablename__ = 'products'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nama_produk = db.Column(
        db.String(150),
        nullable=False
    )

    deskripsi = db.Column(
        db.Text
    )

    harga = db.Column(
        db.BigInteger,
        nullable=False
    )

    stok = db.Column(
        db.Integer,
        default=0
    )

    gambar = db.Column(
        db.String(255)
    )

    # Foreign Key Category
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.id')
    )

    # Relationship
    category = db.relationship(
        'Category',
        backref='products'
    )