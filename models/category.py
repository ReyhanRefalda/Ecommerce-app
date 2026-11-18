from extensions import db

class Category(db.Model):

    __tablename__ = 'categories'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nama_kategori = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )