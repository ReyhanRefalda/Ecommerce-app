from flask import Flask
from flask_login import LoginManager
from datetime import datetime
import pytz

from models.user import db, User
from models.cart import Cart
from models.order import Order
from models.order_item import OrderItem
from models.category import Category
from models.notification import Notification
from utils.error_handlers import register_error_handlers
from routes.notification_routes import notification_bp


# Admin Routes
from routes.auth_routes import auth
from routes.admin.dashboard_routes import dashboard
from routes.admin.product_admin_routes import product
from routes.admin.payment_admin_routes import payment_admin
from routes.admin.order_admin_routes import order_admin
from routes.admin.user_admin_routes import user_admin
from routes.admin.category_admin_routes import category_admin

# User Routes
from routes.landing_routes import landing
from routes.product_routes import product_bp
from routes.cart_routes import cart_bp
from routes.checkout_routes import checkout_bp
from routes.order_routes import order_bp


app = Flask(__name__)

# Secret Key
app.secret_key = 'secretkey'

# Upload Config
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ecommerce_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init Database
db.init_app(app)

# Flask Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register Blueprint
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(product) 
app.register_blueprint(payment_admin)# admin product
app.register_blueprint(order_admin)
app.register_blueprint(user_admin)
app.register_blueprint(category_admin)

app.register_blueprint(landing)
app.register_blueprint(product_bp)   # user product
app.register_blueprint(cart_bp)
app.register_blueprint(checkout_bp)
app.register_blueprint(order_bp)
app.register_blueprint(notification_bp)

register_error_handlers(app)

@app.template_filter('wib_date')
def wib_date(value):
    if not value:
        return "—"

    jakarta = pytz.timezone('Asia/Jakarta')

    # jika datetime naive (UTC dari DB)
    if value.tzinfo is None:
        value = pytz.utc.localize(value)

    value = value.astimezone(jakarta)

    return value.strftime("%d %b %Y %H:%M WIB")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)