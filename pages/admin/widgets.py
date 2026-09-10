"""Custom form widgets used across Product admin and Project admin.

These widgets render JSONField values (specs / energy_data / ordering_info /
translations) as structured HTML inputs instead of raw JSON, so non-technical
admins can edit the data without touching JSON syntax.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0 so the
admin module is one model per file.
"""
import json

from django import forms
from django.conf import settings
from django.utils.html import escape, mark_safe


# ---------------------------------------------------------------------------
# SpecsWidget — 6 自由 label/value 对（产品参数表，最多 6 行 × 4 列 = 24 项，
# 前台显示为 2 列 × 3 行）
# ---------------------------------------------------------------------------
class SpecsWidget(forms.Widget):
    """Render the flexible specs JSON as 6 label/value input pairs."""

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                value = []
        if not isinstance(value, list):
            value = []
        while len(value) < 6:
            value.append({})
        value = value[:6]

        inputs = []
        for i, spec in enumerate(value):
            label = spec.get('label', '') if isinstance(spec, dict) else ''
            val = spec.get('value', '') if isinstance(spec, dict) else ''
            inputs.append(
                f'<input type="text" name="{name}_{i}_label" value="{escape(label)}" '
                f'placeholder="Label {i + 1}" style="padding:6px 8px;border:1px solid #ccc;border-radius:4px;width:100%;box-sizing:border-box;">'
                f'<input type="text" name="{name}_{i}_value" value="{escape(val)}" '
                f'placeholder="Value {i + 1}" style="padding:6px 8px;border:1px solid #ccc;border-radius:4px;width:100%;box-sizing:border-box;">'
            )
        return mark_safe(
            f'<div style="max-width:900px;">'
            f'<p style="margin:0 0 10px;color:#666;font-size:12px;">'
            f'最多 6 组参数，每行 2 组（4 列），共 3 行，与前台显示一致。</p>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px 12px;">'
            f'{"".join(inputs)}'
            f'</div></div>'
        )

    def value_from_datadict(self, data, files, name):
        specs = []
        for i in range(6):
            label = data.get(f'{name}_{i}_label', '').strip()
            value = data.get(f'{name}_{i}_value', '').strip()
            if label or value:
                specs.append({'label': label, 'value': value})
        return json.dumps(specs)


# ---------------------------------------------------------------------------
# EnergyDataWidget — 17 个固定参数的详情页 ENERGY AND PERFORMANCE DATA 表
# ---------------------------------------------------------------------------
ENERGY_DATA_FIELDS = [
    'Series Name',
    'Lumen Output',
    'System Wattage',
    'CRI',
    'Color Temperature (Kevin)',
    'Input Voltage (High Voltage)',
    'Input Voltage (Low Voltage)',
    'L70 Hours',
    'Operating Temperature Range',
    'Surge (Common Mode / Differential Mode)',
    'IP Rating',
    'Effective Projected Area (EPA) at 90°',
    'L" × W" × H"',
    'Approximate Weight',
    'Material',
    'LED Brand',
    'LED Driver',
]


class EnergyDataWidget(forms.Widget):
    """Render the energy & performance data JSON as 17 pre-labeled input rows."""

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                value = []
        if not isinstance(value, list):
            value = []

        # Build a dict from existing data for quick lookup
        data_dict = {}
        for item in value:
            if isinstance(item, dict) and item.get('label'):
                data_dict[item['label']] = item.get('value', '')

        rows = []
        for i, label in enumerate(ENERGY_DATA_FIELDS):
            val = escape(data_dict.get(label, ''))
            rows.append(
                f'<div style="display:flex;gap:8px;align-items:center;margin-bottom:4px;">'
                f'<input type="hidden" name="{name}_{i}_label" value="{escape(label)}">'
                f'<span style="width:320px;font-size:12px;color:#333;flex-shrink:0;">{escape(label)}</span>'
                f'<input type="text" name="{name}_{i}_value" value="{val}" '
                f'placeholder="输入值…" style="flex:1;padding:5px 8px;border:1px solid #ccc;border-radius:4px;box-sizing:border-box;font-size:12px;">'
                f'</div>'
            )
        return mark_safe(
            f'<div style="max-width:760px;padding:8px 0;">'
            f'<p style="margin:0 0 10px;color:#666;font-size:12px;">'
            f'以下是 17 个标准参数，填写 value（值）即可。留空则不显示该行。</p>'
            f'{"".join(rows)}'
            f'</div>'
        )

    def value_from_datadict(self, data, files, name):
        specs = []
        for i in range(len(ENERGY_DATA_FIELDS)):
            label = data.get(f'{name}_{i}_label', '').strip()
            value = data.get(f'{name}_{i}_value', '').strip()
            if value:  # Only include rows that have a value filled in
                specs.append({'label': label, 'value': value})
        return json.dumps(specs)


# ---------------------------------------------------------------------------
# OrderingInfoWidget — 9 列订购信息表（含 Fill Defaults 按钮 + 17 列布局）
# ---------------------------------------------------------------------------
ORDERING_COLUMNS = [
    'Series Name',
    'System Power',
    'CCT',
    'Input Voltage',
    'Beam Angle',
    'Finish (option)',
    'Dimming (option)',
    'Bracket Type (option)',
    'LED Driver Location',
]

ORDERING_DEFAULTS = [
    "FL1M (Light With 1 Module)",
    "80W",
    "30=3000K\n40=4000K\n57=5700K",
    "S=Standard Voltage (110-277VAC)\nH=High Voltage (347-480VAC)",
    "12=12°\n18=18°\n30=30°\n50=50°",
    "GRY=Grey\nBLK=Black",
    "1.0-10V\n2. DMX\n3. DALI\n4.Zigbee",
    "U = Hang Mount Bracket\nL = Sitting Mount Bracket",
    "W = With Fixture\nS = Separated from Fixture",
]


class OrderingInfoWidget(forms.Widget):
    """Render the ordering_info JSON as 9 columns matching the frontend table layout."""

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                value = []
        if not isinstance(value, list):
            value = []
        while len(value) < 9:
            value.append('')

        columns_html = []
        for i, header in enumerate(ORDERING_COLUMNS):
            val = escape(value[i] if i < len(value) else '')
            col_style = 'min-width:130px;flex:1;'
            if header == 'Beam Angle':
                col_style = 'min-width:130px;flex:1.3;'
            elif header == 'Dimming (option)':
                col_style = 'min-width:90px;flex:0.7;'
            columns_html.append(
                f'<div style="{col_style}">'
                f'<div style="font-size:10px;font-weight:700;color:#333;text-align:center;margin-bottom:4px;min-height:28px;display:flex;align-items:flex-end;justify-content:center;">{escape(header)}</div>'
                f'<textarea name="{name}_{i}" rows="4" '
                f'style="width:100%;padding:4px 6px;border:1px solid #ccc;border-radius:3px;'
                f'box-sizing:border-box;font-size:11px;font-family:monospace;resize:vertical;text-align:center;">{val}</textarea>'
                f'</div>'
            )
        return mark_safe(
            f'<div style="max-width:100%;padding:8px 0;overflow-x:auto;">'
            f'<p style="margin:0 0 10px;color:#666;font-size:12px;">'
            f'每列支持多行（换行分隔），留空列不显示。横向滚动查看全部 9 列。</p>'
            f'<div class="ordering-fill-row" style="margin-bottom:10px;display:flex;align-items:center;gap:12px;">'
            f'<button type="button" class="button ordering-fill-btn" '
            f'data-defaults="{escape(json.dumps(ORDERING_DEFAULTS, ensure_ascii=False))}" '
            f'style="white-space:nowrap;">🔄 Fill Defaults</button>'
            f'<span class="ordering-fill-status" style="font-size:12px;color:#666;"></span>'
            f'</div>'
            f'<div style="display:flex;gap:6px;min-width:1000px;">'
            f'{"".join(columns_html)}'
            f'</div></div>'
        )

    def value_from_datadict(self, data, files, name):
        values = []
        for i in range(9):
            val = data.get(f'{name}_{i}', '').strip()
            values.append(val)
        while values and not values[-1]:
            values.pop()
        return json.dumps(values)


# ---------------------------------------------------------------------------
# TranslationsWidget — 每语种一个 textarea + auto-translate 按钮
# ---------------------------------------------------------------------------
class TranslationsWidget(forms.Widget):
    """Render translations as one textarea per language with per-language auto-translate buttons.

    Each language textarea contains a small JSON object for that language, e.g.
    {"title": "..", "description": "..", "results": ".."}
    Value_from_datadict assembles the per-language JSON into the model's translations dict.
    """

    def __init__(self, attrs=None):
        self.attrs = attrs or {}
        super().__init__(attrs=self.attrs)

    def render(self, name, value, attrs=None, renderer=None):
        # value is expected to be a dict: { 'fr': {...}, 'es': {...} }
        import json as _json

        val = value or {}
        try:
            # if stored as string
            if isinstance(val, str):
                val = _json.loads(val)
        except Exception:
            val = {}

        parts = []
        # iterate settings.LANGUAGES but skip English (source)
        # Render languages in the fixed order preferred for the admin UI
        desired_order = ['fr', 'es', 'de', 'ru', 'ar']
        # Build a lookup of language display names from settings.LANGUAGES
        lang_names = {code: name for code, name in getattr(settings, 'LANGUAGES', [])}
        for code in desired_order:
            lang_name = lang_names.get(code, code)
            lang_obj = val.get(code) or {}
            lang_json = _json.dumps(lang_obj, ensure_ascii=False, indent=2)
            textarea_id = f'id_translations_{code}'
            parts.append(
                f'<div class="translation-lang" style="display:block;width:100% !important;max-width:900px;box-sizing:border-box;margin-bottom:14px;">'
                f'<label for="{textarea_id}" style="display:block;font-weight:700;margin-bottom:6px;">{code} — {escape(lang_name)}</label>'
                f'<textarea id="{textarea_id}" name="{name}_{code}" rows="{self.attrs.get("rows", "6")}" '
                f'style="width:100% !important;max-width:900px;box-sizing:border-box;font-family:monospace;font-size:12px;">{escape(lang_json)}</textarea>'
                f'<div class="auto-translate-row" style="margin:8px 0 6px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
                f'<button type="button" class="button auto-translate-btn" data-lang="{code}" data-target-id="{textarea_id}" '
                f'style="white-space:nowrap;">🔄 Auto-Translate {escape(lang_name)}</button>'
                f'<span class="auto-translate-status" style="font-size:12px;color:#666;"></span>'
                f'</div></div>'
            )

        return mark_safe(''.join(parts))

    def value_from_datadict(self, data, files, name):
        # Assemble per-language JSON values into a dict
        import json as _json

        translations = {}
        for code, _ in getattr(settings, 'LANGUAGES', []):
            if code == 'en':
                continue
            raw = data.get(f'{name}_{code}', '').strip()
            if not raw:
                continue
            try:
                parsed = _json.loads(raw)
                if isinstance(parsed, dict):
                    translations[code] = parsed
            except Exception:
                # store raw string fallback under 'description' if it's plain text
                translations[code] = {'description': raw}
        return _json.dumps(translations)