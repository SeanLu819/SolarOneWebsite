"""ContactMessageAdmin: read-only-ish view for contact-form submissions.

No add permission (submissions come from public form). Email + subject editable
inline for triage. ``created_at`` is readonly so the original timestamp
survives edits.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
from django.contrib import admin

from pages.models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read',)
    list_editable = ['is_read']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'