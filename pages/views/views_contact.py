import logging
from django.shortcuts import render
from django.contrib import messages
from django.core.cache import cache
from django.conf import settings
from django.utils.translation import gettext as _
from .common import get_common_context

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or '0.0.0.0'


def _is_rate_limited(request):
    window = getattr(settings, 'CONTACT_RATE_WINDOW', 600)
    limit = getattr(settings, 'CONTACT_RATE_LIMIT', 3)
    ip = _get_client_ip(request)
    session_key = request.session.session_key or 'anon'
    key = f'contact_rate:{ip}:{session_key}'
    try:
        count = cache.get(key) or 0
        if count >= limit:
            return True
        cache.set(key, count + 1, timeout=window)
    except Exception:
        logger.warning('Rate limit cache unavailable, failing open', exc_info=True)
        return False
    return False


def _send_contact_notification(contact_msg):
    notify_to = getattr(settings, 'CONTACT_NOTIFY_EMAIL', '')
    if not notify_to:
        return False
    subject = f'[Contact] New message from {contact_msg.name}'
    body_lines = [
        f'Name:    {contact_msg.name}',
        f'Email:   {contact_msg.email}',
        f'Phone:   {contact_msg.phone or "(not provided)"}',
        '',
        'Message:',
        contact_msg.message,
        '',
        f'Submitted at: {contact_msg.created_at:%Y-%m-%d %H:%M:%S}',
        f'Reply URL:    mailto:{contact_msg.email}',
    ]
    try:
        from django.core.mail import send_mail
        send_mail(
            subject=subject,
            message='\n'.join(body_lines),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@solarone.com'),
            recipient_list=[notify_to],
            fail_silently=True,
        )
        return True
    except Exception:
        logger.warning('Failed to send contact notification email', exc_info=True)
        return False


def contact(request):
    context = get_common_context()

    prefill_product = request.GET.get('product', '').strip()
    prefill_product_name = request.GET.get('product_name', '').strip()
    prefill_ref = request.GET.get('ref', '').strip()

    if prefill_product:
        context['prefill_product'] = prefill_product
        context['prefill_product_name'] = prefill_product_name
        context['prefill_ref'] = prefill_ref

    if request.method == 'POST':
        if _is_rate_limited(request):
            messages.error(
                request,
                _('Too many messages submitted recently. Please wait a few minutes before trying again.')
            )
            return render(request, 'contact.html', context)

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        message = request.POST.get('message', '').strip()
        product_name = request.POST.get('product_name', '').strip()
        if name and email and message:
            try:
                from pages.models import ContactMessage
                contact_msg = ContactMessage.objects.create(
                    name=name, email=email, phone=phone, message=message
                )
                _send_contact_notification(contact_msg)
                messages.success(request, _('Your message has been sent successfully!'))
            except Exception:
                logger.warning('Failed to save contact message', exc_info=True)
                messages.error(request, _('Sorry, we could not save your message. Please try again.'))
    return render(request, 'contact.html', context)