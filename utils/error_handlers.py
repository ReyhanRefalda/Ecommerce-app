

from flask import render_template
from flask_login import current_user


def register_error_handlers(app):

    @app.errorhandler(403)
    def forbidden_error(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template('errors/404.html'), 404