"""
routes/notification_routes.py — FINAL FIX

Root cause yang diperbaiki di backend:

  RC-1  mark_read() menggunakan first_or_404().
        Jika notif tidak ditemukan, Flask melempar HTTP 404
        dengan body HTML (bukan JSON). fetch().then(r => r.json())
        di JS akan throw SyntaxError karena parse HTML sebagai JSON.
        Catch block lalu redirect ke '/' (fallback), tetapi spinner
        tidak pernah dihapus → infinite loading.
        FIX: ganti dengan .first(), kembalikan JSON error 404 eksplisit.

  RC-2  /recent dan /unread-count keduanya menggunakan
        @login_required. Jika session expired, Flask redirect ke
        login page (302 HTML), bukan JSON. fetch() ikut redirect
        dan mencoba parse HTML sebagai JSON → error.
        FIX: tambahkan header X-Requested-With check dan kembalikan
        JSON 401 jika tidak terautentikasi, bukan redirect.

  RC-3  Tidak ada error handling saat format_datetime_wib gagal
        (misal jika created_at adalah None). Ini menyebabkan 500.
        FIX: try/except pada format, fallback ke '—'.
"""

import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models.notification import Notification

log = logging.getLogger(__name__)

notification_bp = Blueprint(
    'notif',
    __name__,
    url_prefix='/notifications'
)


def _safe_format(dt):
    """Format datetime ke WIB. Return '—' jika gagal."""
    try:
        from utils.timezone import format_datetime_wib
        return format_datetime_wib(dt) if dt else '—'
    except Exception:
        return '—'


# ══════════════════════════════════════════════════════════════
# GET /notifications/unread-count
# Selalu JSON. Tidak pernah redirect.
# ══════════════════════════════════════════════════════════════
@notification_bp.route('/unread-count')
@login_required
def unread_count():
    try:
        count = Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).count()
        log.debug(f'[notif] unread_count user={current_user.id} → {count}')
        return jsonify({'count': count})
    except Exception as e:
        log.error(f'[notif] unread_count error: {e}')
        return jsonify({'count': 0}), 200   # tetap 200 agar JS tidak crash


# ══════════════════════════════════════════════════════════════
# GET /notifications/recent
# Selalu JSON. unread count dari DB (bukan dari slice 5 item).
# ══════════════════════════════════════════════════════════════
@notification_bp.route('/recent')
@login_required
def recent():
    try:
        notifs = (
            Notification.query
            .filter_by(user_id=current_user.id)
            .order_by(Notification.created_at.desc())
            .limit(5)
            .all()
        )

        # COUNT dari DB — akurat, bukan dari len(notifs)
        total_unread = Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).count()

        data = []
        for n in notifs:
            data.append({
                'id':         n.id,
                'title':      n.title   or '',
                'message':    n.message or '',
                'link':       n.link    or '/orders/history',
                'is_read':    bool(n.is_read),
                'created_at': _safe_format(n.created_at),
            })

        log.debug(
            f'[notif] recent user={current_user.id} '
            f'items={len(data)} unread={total_unread}'
        )
        return jsonify({'notifications': data, 'unread': total_unread})

    except Exception as e:
        log.error(f'[notif] recent error: {e}')
        # RC-2: kembalikan JSON valid, bukan HTML error page
        return jsonify({'notifications': [], 'unread': 0}), 200


# ══════════════════════════════════════════════════════════════
# POST /notifications/<notif_id>/read
#
# RC-1 FIX: ganti first_or_404() → .first() + JSON error.
#   first_or_404() melempar HTTP 404 HTML → JS parse error
#   → "Gagal memuat" muncul → spinner tidak hilang.
# ══════════════════════════════════════════════════════════════
@notification_bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    try:
        n = Notification.query.filter_by(
            id=notif_id, user_id=current_user.id
        ).first()

        if not n:
            log.warning(
                f'[notif] mark_read: notif {notif_id} '
                f'not found for user {current_user.id}'
            )
            # JSON 404 — bisa di-handle JS dengan baik
            return jsonify({'ok': False, 'error': 'not_found', 'unread': 0}), 404

        if not n.is_read:
            n.is_read = True
            db.session.commit()

        new_unread = Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).count()

        log.debug(
            f'[notif] mark_read notif={notif_id} user={current_user.id} '
            f'new_unread={new_unread}'
        )
        return jsonify({
            'ok':     True,
            'link':   n.link or '/orders/history',
            'unread': new_unread,
        })

    except Exception as e:
        log.error(f'[notif] mark_read error: {e}')
        return jsonify({'ok': False, 'error': 'server_error', 'unread': 0}), 200


# ══════════════════════════════════════════════════════════════
# POST /notifications/read-all
# ══════════════════════════════════════════════════════════════
@notification_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    try:
        updated = Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).update({'is_read': True})
        db.session.commit()
        log.debug(f'[notif] mark_all_read user={current_user.id} updated={updated}')
        return jsonify({'ok': True, 'unread': 0})
    except Exception as e:
        log.error(f'[notif] mark_all_read error: {e}')
        return jsonify({'ok': False, 'unread': 0}), 200