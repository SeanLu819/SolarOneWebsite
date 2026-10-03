"""Legacy URL → canonical URL redirects (301).

Single source of truth is **this module** — not the database and not
``seed_data.json``. Redirects are routing configuration, and production runs
stateless off the seed (``IS_VERCEL``); a table that lived in the DB would be
invisible there, and one that lived in the seed would have to pay the DB/seed
double-write that every content field already pays. Keeping it here also lets
the guard tests assert the table is self-consistent with no fixture at all.

"Page moved" happens at three different levels, so there are three tables:

``PROJECT_SLUG_REDIRECTS`` / ``PRODUCT_SLUG_REDIRECTS``
    Page was renamed, content is otherwise identical. Key is the **old** slug,
    value the current one. Consulted inside the detail views *only when the
    requested slug fails to resolve*, so registering a redirect can never
    shadow a page that still exists.

``LEGACY_PATH_REDIRECTS``
    A whole route was retired. Key is the old path — relative, no leading
    slash, no language prefix. Value is a **URL name**, not a path string, on
    purpose: the target gets reversed, so a visitor on ``/fr/`` lands on
    ``/fr/…``. Hard-coding ``'/about/'`` here would silently drop them back
    into English. (It is a name rather than ``(name, kwargs)`` because
    ``RedirectView.as_view()`` cannot be passed ``kwargs`` — see
    ``tests_redirects``. Parameterised legacy routes would need ``re_path``.)

Adding an entry is the entire job — no view, URL or template change. What an
entry does **not** do is move content: images live under
``static/images/projects/<slug>/`` and are fixed at upload time, so renaming a
slug also means moving that directory and updating ``project_detail.html``'s
hard-coded slug branches. See ``OPTIMIZATION_PLAN.md`` §B3.
"""

# --------------------------------------------------------------------------
# Tables. Empty is the correct state: every entry is a decision that content
# has actually moved, and inventing one would send crawlers to a 404.
# --------------------------------------------------------------------------

#: Old project slug → current project slug.
PROJECT_SLUG_REDIRECTS = {}

#: Old product slug → current product slug.
PRODUCT_SLUG_REDIRECTS = {}

#: Old path (no language prefix, no leading slash) → URL name to reverse.
#:
#: The three retired sports keyword landing pages. They were purpose-built for
#: keywords rather than around real content, so they 301 to pages that carry the
#: same intent on honest URLs: the football/tennis collections list the actual
#: projects, and the stadium hub folds back into the catalogue (the VSP product
#: titles already carry "LED Stadium Light").
#: Note the targets are *bare URL names* — this table cannot express
#: ``/projects/?sport=…``, and a filtered URL would be self-defeating anyway:
#: canonical is built from ``request.path``, which drops the query string, so
#: every filtered URL canonicalises to /projects/ and the keyword never owns a
#: distinct indexable URL.
LEGACY_PATH_REDIRECTS = {
    'products/sports-lighting/': 'products',
    'products/football-stadium-lights/': 'projects_football',
    'products/tennis-court-lighting/': 'projects_tennis',
}


def redirect_target_for_project(slug):
    """Current project slug for a retired one, or ``None``."""
    return PROJECT_SLUG_REDIRECTS.get(slug or '')


def redirect_target_for_product(slug):
    """Current product slug for a retired one, or ``None``."""
    return PRODUCT_SLUG_REDIRECTS.get(slug or '')


def legacy_path_entries():
    """``(route, url_name)`` pairs, ordered for reproducible URLs.

    Consumed by ``pages/urls.py`` to synthesise ``RedirectView`` routes ahead
    of everything else — a catch-all like ``products/<slug:slug>/`` would
    otherwise swallow the legacy path before the redirect ever runs.
    """
    return list(sorted(LEGACY_PATH_REDIRECTS.items()))


def redirect_table_problems(project_slugs=(), product_slugs=()):
    """Return a list of human-readable problems with the tables.

    Empty list means sane. Callers pass the slug sets they know about (seed or
    DB) so targets can be checked for existence; omitting them skips that
    check rather than guessing.

    A redirect whose target is itself a redirect source is rejected: chains
    cost an extra round trip per hop and Google stops following after ~5.
    """
    problems = []

    def _check(table, label, known):
        for old, new in sorted(table.items()):
            if not old or not isinstance(old, str):
                problems.append(f'{label}: empty or non-string source {old!r}')
                continue
            if not new or not isinstance(new, str):
                problems.append(f'{label}: {old!r} → empty/non-string target {new!r}')
                continue
            if old == new:
                problems.append(f'{label}: {old!r} redirects to itself')
                continue
            if new in table:
                problems.append(
                    f'{label}: {old!r} → {new!r} is a chain ({new!r} is itself a source)')
                continue
            if known is not None and new not in known:
                problems.append(f'{label}: {old!r} → {new!r} but no such slug exists')

    _check(PROJECT_SLUG_REDIRECTS, 'PROJECT_SLUG_REDIRECTS',
           set(project_slugs) if project_slugs else None)
    _check(PRODUCT_SLUG_REDIRECTS, 'PRODUCT_SLUG_REDIRECTS',
           set(product_slugs) if product_slugs else None)

    for route, name in sorted(LEGACY_PATH_REDIRECTS.items()):
        if not route or route.startswith('/') or not route.endswith('/'):
            problems.append(
                f'LEGACY_PATH_REDIRECTS: {route!r} must be relative and end with "/"')
            continue
        if not name or not isinstance(name, str):
            problems.append(f'LEGACY_PATH_REDIRECTS: {route!r} has empty url_name')

    return problems
