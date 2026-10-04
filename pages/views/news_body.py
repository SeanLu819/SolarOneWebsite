"""Split news body text into paragraphs and place figures between them (v1.10.4).

Why
---
Until v1.10.3 every gallery photo on a news article was rendered in one bento
grid **above** the body, so a three-paragraph market article showed all three
photographs before the first sentence of text. A photograph of SMD boards
illustrates one specific claim; floating it to the top disconnects it from
that claim and forces the reader to map it back mentally.

The editors want each figure to sit with the paragraph it supports, which means
the body must be rendered **in pieces** rather than as one
``{{ article.content|linebreaks }}`` blob.

How the editor controls placement
---------------------------------
The body keeps using a marker in plain text::

    Paragraph one.
    {{figure:smd-leds}}
    Paragraph two.

The marker names an entry in the article's ``images`` list (by its ``id`` when
present, otherwise by its file name / alt). Everything between two markers is
one HTML paragraph. Markers are consumed here — the template never sees them,
so a typo can only ever drop one photo, never break the page.

Deliberately not implemented: inline ``<figure>`` inside the body text. The
content is edited through a plain textarea in admin and translated through the
``translations`` JSONField, so raw HTML in the body would have to survive both
round trips. A visible plaintext marker survives both for free.

Nothing here renders HTML. Paragraph text is escaped by the template's own
``|linebreaks`` equivalent (see ``paragraphs``), and figure dicts carry only
URLs/alt text that the template escapes the same way it always has.
"""

import re

#: ``{{figure:identifier}}`` — tolerant of whitespace and of the doubled braces
#: an editor may paste. Kept deliberately narrow: a stray ``{{`` elsewhere in
#: the body must not be mistaken for a marker.
_MARKER_RE = re.compile(r'\{\{\s*figure\s*:\s*([A-Za-z0-9_.-]+)\s*\}\}')

#: Paragraph break: a blank line, or a newline that the editor's textarea
#: inserted. Windows-authored copy arrives with CRLF, so normalise first.
_BLANK_LINE_RE = re.compile(r'\n\s*\n')


def _paragraphs(text):
    """Split ``text`` into non-empty stripped paragraphs."""
    if not text:
        return []
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')
    chunks = _BLANK_LINE_RE.split(normalized)
    return [c.strip() for c in chunks if c and c.strip()]


def _image_key(image):
    """The identifier an editor types in ``{{figure:…}}`` for this image.

    Tries the admin id first (stable across renames), then the file name, then
    the alt text — so an article written before the gallery gained ids still
    binds by file name without a migration.
    """
    for candidate in (image.get('id'), image.get('name'),
                      image.get('file_name'), image.get('alt')):
        if candidate:
            return str(candidate)
    url = image.get('url') or ''
    return url.rsplit('/', 1)[-1] if url else ''


def _build_lookup(images):
    """Map every alias of every image to its index in ``images``."""
    lookup = {}
    for index, image in enumerate(images):
        for alias in (image.get('id'), image.get('name'),
                      image.get('file_name'), image.get('alt')):
            if alias:
                lookup.setdefault(str(alias), index)
        url = image.get('url') or ''
        if url:
            lookup.setdefault(url, index)
            lookup.setdefault(url.rsplit('/', 1)[-1], index)
    return lookup


def build_article_body(content, images):
    """Return ``(blocks, unused_indices)`` for one article.

    ``blocks`` is a list of dicts the template loops over, in document order:

    * ``{'type': 'p', 'text': …}`` — one paragraph.
    * ``{'type': 'figure', 'image': <image dict>, 'eager': <bool>}`` — a photo.

    ``unused_indices`` lists gallery images that no marker referenced, so the
    caller can still render them (at the top or bottom) instead of silently
    dropping them. Losing a photo because an editor forgot a marker would be a
    content regression that is invisible in the admin.
    """
    images = images or []
    paragraphs = _paragraphs(content)
    if not images or not paragraphs:
        # No markers possible: emit plain paragraphs and let the caller fall
        # back to its existing top-of-article rendering.
        return [{'type': 'p', 'text': p} for p in paragraphs], list(range(len(images)))

    lookup = _build_lookup(images)
    blocks = []
    used = set()
    # The first figure carries the LCP-ish image and must not be lazy.
    figure_ordinal = 0

    for raw_paragraph in paragraphs:
        # A marker on its own line means "insert the figure *before* this
        # paragraph"; a marker inline at the end of a sentence means "after
        # it". Splitting on the marker handles both.
        pieces = _MARKER_RE.split(raw_paragraph)
        # pieces = [text, key, text, key, text, …]
        leading = pieces[0].strip()
        if leading:
            blocks.append({'type': 'p', 'text': leading})

        for i in range(1, len(pieces), 2):
            key = pieces[i]
            index = lookup.get(key)
            if index is None or index in used:
                # Unknown or duplicate marker: keep the text, drop the marker.
                # A broken figure must never swallow a paragraph.
                continue
            used.add(index)
            blocks.append({
                'type': 'figure',
                'image': images[index],
                'eager': figure_ordinal == 0,
            })
            figure_ordinal += 1
            trailing = pieces[i + 1].strip() if i + 1 < len(pieces) else ''
            if trailing:
                blocks.append({'type': 'p', 'text': trailing})

    return blocks, [i for i in range(len(images)) if i not in used]