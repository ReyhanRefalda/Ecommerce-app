from extensions import db

class OrderItem(db.Model):

    __tablename__ = 'order_items'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey('order.id'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id'),
        nullable=False
    )

    qty = db.Column(
        db.Integer,
        nullable=False
    )

    harga = db.Column(
        db.BigInteger,
        nullable=False
    )

    subtotal = db.Column(
        db.BigInteger,
        nullable=False
    )
    product = db.relationship(
        'Product',
        backref='order_items'
    )