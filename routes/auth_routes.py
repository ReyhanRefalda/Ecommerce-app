from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import re

from models.user import db, User

auth = Blueprint('auth', __name__)


# LOGIN
@auth.route('/login', methods=['GET', 'POST'])
def login():

    error = None

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            error = "Email dan password wajib diisi"

        else:

            user = User.query.filter_by(email=email).first()

            if not user:
                error = "Email tidak ditemukan"

            elif not check_password_hash(user.password, password):
                error = "Password salah"

            else:

                login_user(user)

                flash(
                    f'Selamat datang, {user.nama}',
                    'success'
                )

                if user.role == 'admin':
                    return redirect(
                        url_for('dashboard.index')
                    )

                return redirect(
                    url_for('landing.index')
                )

    return render_template(
        'auth/login.html',
        error=error
    )


# REGISTER
@auth.route('/register', methods=['GET', 'POST'])
def register():

    error = None

    if request.method == 'POST':

        nama = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not nama:
                error = "Nama lengkap wajib diisi"

        elif len(nama) < 3:
                error = "Nama minimal 3 karakter"

        elif not username:
                error = "Username wajib diisi"

        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
                error = "Username hanya boleh huruf, angka dan underscore"

        elif not email:
                error = "Email wajib diisi"

        elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            error = "Format email tidak valid"

        elif len(password) < 8:
                error = "Password minimal 8 karakter"

        elif password != confirm_password:
                error = "Konfirmasi password tidak cocok"

        elif User.query.filter_by(username=username).first():
                error = "Username sudah digunakan"

        elif User.query.filter_by(email=email).first():
                error = "Email sudah digunakan"

        else:

            hashed_password = generate_password_hash(password)

            user = User(
                nama=nama,
                username=username,
                email=email,
                password=hashed_password
            )

            db.session.add(user)
            db.session.commit()

            flash(
                'Registrasi berhasil, silakan login',
                'success'
            )

            return redirect(
                url_for('auth.login')
            )

    return render_template(
        'auth/register.html',
        error=error
    )


# LOGOUT
@auth.route('/logout')
def logout():

    logout_user()

    flash(
        'Berhasil logout',
        'success'
    )

    return redirect(
        url_for('auth.login')
    )