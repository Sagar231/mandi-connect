import csv
import io

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage, send_mail
from django.utils import timezone


def _uid(user):
    from users.views import make_uid

    return make_uid(user)


@shared_task
def send_verification_email(user_id):
    from common.tokens import email_verification_token

    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return
    token = email_verification_token.make_token(user)
    link = f"{settings.FRONTEND_BASE_URL}/verify-email/?uid={_uid(user)}&token={token}"
    send_mail(
        "Verify your MandiConnect account",
        f"Welcome to MandiConnect!\n\nVerify your email: {link}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )


@shared_task
def send_password_reset_email(user_id):
    from common.tokens import password_reset_token

    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return
    token = password_reset_token.make_token(user)
    link = f"{settings.FRONTEND_BASE_URL}/reset-password/?uid={_uid(user)}&token={token}"
    send_mail(
        "Reset your MandiConnect password",
        f"Reset your password here: {link}\n\nIgnore if you didn't request this.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )


@shared_task
def check_price_alerts(product_id, new_price):
    """Triggered after a price listing changes. Emails users whose threshold is met."""
    from decimal import Decimal

    from .models import PriceAlert

    new_price = Decimal(str(new_price))
    alerts = PriceAlert.objects.filter(
        product_id=product_id, is_active=True, threshold__gte=new_price
    ).select_related("user", "product")
    triggered = 0
    for alert in alerts:
        send_mail(
            f"Price drop: {alert.product.name}",
            f"{alert.product.name} is now {new_price} "
            f"(your alert threshold was {alert.threshold}).",
            settings.DEFAULT_FROM_EMAIL,
            [alert.user.email],
            fail_silently=True,
        )
        alert.last_triggered_at = timezone.now()
        alert.save(update_fields=["last_triggered_at"])
        triggered += 1
    return triggered


@shared_task
def export_price_list_csv(user_id, market_id=None):
    """Generate a CSV of current prices and email it to the user."""
    from pricing.models import PriceListing

    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return
    qs = PriceListing.objects.filter(is_active=True).select_related(
        "vendor", "product", "vendor__market"
    )
    if market_id:
        qs = qs.filter(vendor__market_id=market_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Market", "Vendor", "Product", "Unit", "Price", "Stock", "Date"])
    for listing in qs:
        writer.writerow(
            [
                listing.vendor.market.name,
                listing.vendor.shop_name,
                listing.product.name,
                listing.product.unit,
                listing.price,
                listing.stock_status,
                listing.date,
            ]
        )
    email = EmailMessage(
        "Your MandiConnect price-list export",
        "Attached is your requested price list.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    email.attach("price_list.csv", buffer.getvalue(), "text/csv")
    email.send(fail_silently=True)
    return qs.count()
