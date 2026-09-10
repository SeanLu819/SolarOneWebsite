"""admin_translate view: bulk MyMemory translate for Product/Project fields.

Endpoint: POST /admin/translate/
Auth:     @staff_member_required
Body:     {"fields": {"name": "...", "description": "..."}, "target_lang": "fr"}
Response: {"translations": {"fr": {"name": "...", ...}, ...}}

Used by ``admin/js/auto_translate.js`` to populate the per-language
TranslationsWidget textareas in Product / Project admin forms.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
import json as _json
import logging
import random
import time

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


TARGET_LANGS = ['fr', 'es', 'de', 'ru', 'ar']

LANG_NAMES = {
    'fr': 'French',
    'es': 'Spanish',
    'de': 'German',
    'ru': 'Russian',
    'ar': 'Arabic',
}


@staff_member_required
@require_POST
def admin_translate(request):
    try:
        data = _json.loads(request.body)
        fields = data.get('fields', {})
        target_lang = data.get('target_lang')
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not fields:
        return JsonResponse({'error': 'No fields to translate'}, status=400)

    from deep_translator import MyMemoryTranslator

    LANG_MAP = {
        'fr': 'fr-FR',
        'es': 'es-ES',
        'de': 'de-DE',
        'ru': 'ru-RU',
        'ar': 'ar-SA',
    }

    def _split_text(text, max_len=480):
        """Split text into chunks at sentence boundaries, max 480 chars each."""
        if len(text) <= max_len:
            return [text]
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            split_at = text.rfind('. ', 0, max_len)
            if split_at == -1:
                split_at = text.rfind('; ', 0, max_len)
            if split_at == -1:
                split_at = text.rfind(' ', 0, max_len)
            if split_at == -1:
                split_at = max_len
            chunks.append(text[:split_at + 1])
            text = text[split_at + 1:].lstrip()
        return chunks

    def _translate_chunk(translator, text):
        chunks = _split_text(text)
        translated_parts = []
        for chunk in chunks:
            for attempt in range(3):
                try:
                    result = translator.translate(chunk)
                    translated_parts.append(result)
                    break
                except Exception as e:
                    err_msg = str(e).lower()
                    if 'too many requests' in err_msg or '429' in str(e) or 'quota' in err_msg:
                        wait = (attempt + 1) * 5 + random.uniform(1, 3)
                        logger.warning(f'Rate limited, waiting {wait:.1f}s (attempt {attempt+1})')
                        time.sleep(wait)
                        if attempt < 2:
                            continue
                    elif attempt == 0:
                        time.sleep(2)
                        continue
                    logger.error(f'Chunk translate error: {e}')
                    translated_parts.append('[Translation error]')
        return ' '.join(translated_parts)

    # If a single target_lang is specified, only translate to that language.
    to_translate = TARGET_LANGS if not target_lang else [target_lang]

    result = {}
    for idx, lang in enumerate(to_translate):
        result[lang] = {}
        target_code = LANG_MAP.get(lang, lang)
        for field_name, text in fields.items():
            text = (text or '').strip()
            if not text:
                result[lang][field_name] = ''
                continue
            # small spacing between chunks to avoid hammering remote API
            time.sleep(random.uniform(0.5, 1.2))
            try:
                translator = MyMemoryTranslator(source='en-GB', target=target_code)
                translated = _translate_chunk(translator, text)
                result[lang][field_name] = translated
            except Exception as e:
                logger.error(f'Translate error [{lang}/{field_name}]: {e}')
                result[lang][field_name] = '[Translation error]'
        # only pause between languages when doing multiple targets
        if not target_lang and idx < len(to_translate) - 1:
            time.sleep(random.uniform(2.5, 4.5))

    return JsonResponse({'translations': result})