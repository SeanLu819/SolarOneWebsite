"""Visitor / DailyStats admins: read-only analytics views.

``Visitor`` model stores hashed IP (no PII) + UA-parse fields. Admins can
search / filter / date-hierarchy but cannot add or change records — they're
written by ``VisitorTrackingMiddleware`` (non-Vercel only) and the cron job.

``DailyStats`` model stores per-day aggregates. ``bounce_rate`` is computed
inline (total - unique / total) so admins don't need a separate report view.

Both are intentionally read-only to prevent tampering with analytics.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
from django.contrib import admin

from pages.models import Visitor, DailyStats


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'path', 'browser', 'os', 'device', 'country', 'is_unique', 'visited_at')
    list_filter = ('is_unique', 'device', 'browser', 'os', 'visited_at')
    search_fields = ('ip_address', 'path', 'country')
    date_hierarchy = 'visited_at'
    readonly_fields = ('ip_address', 'path', 'referrer', 'user_agent', 'browser', 'browser_version', 'os', 'device', 'country', 'city', 'session_key', 'is_unique', 'visited_at')
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_visits', 'unique_visits', 'bounce_rate')
    readonly_fields = ('date', 'total_visits', 'unique_visits')
    list_per_page = 30
    ordering = ['-date']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def bounce_rate(self, obj):
        if obj.total_visits == 0:
            return "N/A"
        rate = ((obj.total_visits - obj.unique_visits) / obj.total_visits) * 100
        return f"{rate:.1f}%"
    bounce_rate.short_description = "Return Rate"