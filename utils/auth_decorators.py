
from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    """
    Membatasi akses HANYA untuk user dengan role == 'admin'.
    Jika user biasa (role == 'user') mencoba akses, tampilkan 403.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def user_required(f):
    """
    Membatasi akses HANYA untuk user dengan role == 'user'.
    Admin TIDAK boleh mengakses halaman milik user biasa
    seperti Cart, Checkout, Buy Now, Order History pribadi.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if current_user.role != 'user':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function