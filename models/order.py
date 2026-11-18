from extensions import db
from datetime import datetime

class Order(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    total_harga = db.Column(
        db.BigInteger,
        nullable=False
    )

    metode_pembayaran = db.Column(
        db.String(50)
    )

    bukti_pembayaran = db.Column(
        db.String(255)
    )

    status = db.Column(
        db.String(50),
        default='Pending Payment'
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # TAMBAHAN
    items = db.relationship(
        'OrderItem',
        backref='order',
        lazy=True
    )