

import logging
from extensions import db
from models.notification import Notification

log = logging.getLogger(__name__)

# ── Map status → (title, message_template, link) ──────────────
_STATUS_MESSAGES = {
    'Processing': {
        'title':   'Pembayaran Diterima ✓',
        'message': 'Pesanan #{order_id} berhasil diverifikasi dan sedang diproses oleh penjual.',
        'link':    '/orders/history',
    },
    'Completed': {
        'title':   'Pesanan Selesai 🎉',
        'message': 'Pesanan #{order_id} telah selesai. Terima kasih telah berbelanja!',
        'link':    '/orders/history',
    },
    'Rejected': {
        'title':   'Pembayaran Ditolak ✗',
        'message': 'Pembayaran pesanan #{order_id} ditolak. Silakan hubungi kami untuk informasi lebih lanjut.',
        'link':    '/orders/history',
    },
}


def notify_order_status(order):
 
    tmpl = _STATUS_MESSAGES.get(order.status)
    if not tmpl:
        log.debug(
            f'[notif_helper] status={order.status!r} tidak memicu notifikasi'
        )
        return

    order_id_str = f'{order.id:05d}'
    message      = tmpl['message'].format(order_id=f'#{order_id_str}')

    notif = Notification(
        user_id = order.user_id,
        title   = tmpl['title'],
        message = message,
        link    = tmpl['link'],
        is_read = False,
    )
    db.session.add(notif)

    log.info(
        f'[notif_helper] notifikasi dibuat '
        f'order={order.id} user={order.user_id} status={order.status!r}'
    )


def get_unread_count(user_id):
    """Jumlah notifikasi belum dibaca untuk user tertentu."""
    return Notification.query.filter_by(
        user_id=user_id, is_read=False
    ).count()


def get_recent_notifications(user_id, limit=5):
    """5 notifikasi terbaru untuk dropdown navbar."""
    return (
        Notification.query
        .filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )