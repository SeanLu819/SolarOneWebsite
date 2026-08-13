# 保存为 fix_translate.py，然后在项目目录运行: python fix_translate.py

import re

file_path = 'pages/admin.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修改重试次数和延迟
content = content.replace('for attempt in range(2):', 'for attempt in range(3):')
content = content.replace('time.sleep(1)', 'time.sleep(2)')

# 2. 添加 import time, import random 到函数开头
pattern = r'(def admin_translate\(request\):\n    """[^"]*""")'
replacement = r'def admin_translate(request):\n    import json as _json\n    import logging\n    import time\n    import random\n    logger = logging.getLogger(__name__)'
content = re.sub(pattern, replacement, content, count=1)

# 3. 修改主循环，增加语言间延时
old_loop = '''    result = {}
    for lang in TARGET_LANGS:
        result[lang] = {}
        target_code = LANG_MAP.get(lang, lang)
        for field_name, text in fields.items():
            text = (text or '').strip()
            if not text:
                result[lang][field_name] = ''
                continue
            try:
                translator = MyMemoryTranslator(source='en-GB', target=target_code)
                translated = _translate_chunk(translator, text)
                result[lang][field_name] = translated
            except Exception as e:
                logger.error(f'Translate error [{lang}/{field_name}]: {e}')
                result[lang][field_name] = f'[Error: {str(e)[:80]}]'

    return JsonResponse({'translations': result})'''

new_loop = '''    result = {}
    for idx, lang in enumerate(TARGET_LANGS):
        result[lang] = {}
        target_code = LANG_MAP.get(lang, lang)
        for field_name, text in fields.items():
            text = (text or '').strip()
            if not text:
                result[lang][field_name] = ''
                continue
            time.sleep(random.uniform(0.5, 1.2))
            try:
                translator = MyMemoryTranslator(source='en-GB', target=target_code)
                translated = _translate_chunk(translator, text)
                result[lang][field_name] = translated
            except Exception as e:
                logger.error(f'Translate error [{lang}/{field_name}]: {e}')
                result[lang][field_name] = f'[Error: {str(e)[:80]}]'
        if idx < len(TARGET_LANGS) - 1:
            time.sleep(random.uniform(2.5, 4.5))

    return JsonResponse({'translations': result})'''

if old_loop in content:
    content = content.replace(old_loop, new_loop)
    print('✓ Main loop updated')
else:
    print('✗ Main loop pattern not found')

# 4. 修改 _translate_chunk 函数，增加限流检测
old_chunk = '''    def _translate_chunk(translator, text):
        """Translate a single chunk, auto-splitting if needed."""
        chunks = _split_text(text)
        translated_parts = []
        for chunk in chunks:
            for attempt in range(3):
                try:
                    translated_parts.append(translator.translate(chunk))
                    break
                except Exception as e:
                    if attempt == 0:
                        import time
                        time.sleep(2)
                        continue
                    logger.error(f'Chunk translate error: {e}')
                    translated_parts.append(f'[Error: {str(e)[:60]}]')
        return ' '.join(translated_parts)'''

new_chunk = '''    def _translate_chunk(translator, text):
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
                    translated_parts.append(f'[Error: {str(e)[:60]}]')
        return ' '.join(translated_parts)'''

if old_chunk in content:
    content = content.replace(old_chunk, new_chunk)
    print('✓ _translate_chunk updated')
else:
    print('✗ _translate_chunk pattern not found')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! Translation rate limiting improved.')
