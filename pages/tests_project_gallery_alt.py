"""项目画廊 alt 文本守卫 —— v1.9.9

背景（实测结论，2026-10-03）：

`pages/views/enrich.py` 的 DB 分支写的是 ``img.alt_text or _gallery_alt(...)``，
而 seed 分支（`_DictProject`，**生产/Vercel 走这条**）**根本不读 `alt_text`**，
永远用自动生成的 ``"{title} — {location} — view N"``。

于是任何一条非空的 `ProjectImage.alt_text` 都会造成**本地 ≠ 生产**：

    prod : 'Bohemia Manor High School — United States — view 1'   ✅ 有实体名
    local: 'Football Field LED Retrofit — view 1'                 ❌ 实体名丢失

实测有 3 个项目（16 张图）中招：
`baseball-field-led-retrofit` / `football-field-led-retrofit` /
`multi-sport-arena-hd-broadcast`，alt 用的是 **slug 人性化**而不是项目真名
（Bohemia Manor High School / Carroll County Sports Complex /
Andre Vacheresse Stadium 全部没进 alt）。

修法是**清空**这 3 处的 override（不是手写新文案 —— seed 分支不读 alt_text，
写了反而再造一次本地≠生产漂移）。本文件把这个不变量锁死。

🔴 与 `pages/tests_cert_images.py:CertDatabasePathTests` 同一条教训：
本项目**测试库是空的**，断言 DB 内容必须直连真实 `db.sqlite3`（只读），
走 ORM 拿 0 行会让断言恒绿 = 假守卫。
"""
import os
import sqlite3

from django.test import SimpleTestCase

from pages.views.enrich import _enrich_project
from pages.views.utils import _DictProject, _load_seed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite3')


class ProjectGalleryAltTests(SimpleTestCase):
    """生产分支（seed）生成的 alt 必须带上项目真实名称与地点。"""

    def test_seed_project_gallery_alt_carries_the_real_project_name(self):
        """生产口径：每张图 alt 都要含 `project.title`，不能只剩 slug 人性化文本。

        这是当初真正的病灶：alt 写的是 "Football Field LED Retrofit"（来自 slug），
        把 "Bohemia Manor High School" 这个实体名整个丢掉了。
        """
        offenders = []
        checked = 0
        for d in _load_seed().get('projects', []):
            slug = d.get('slug', '')
            dp = _DictProject(d)
            _enrich_project(dp, 'en')
            title = (d.get('title') or '').strip()
            for g in (dp.gallery or []):
                checked += 1
                alt = g.get('alt') or ''
                if title and title not in alt:
                    offenders.append((slug, title, alt))
        self.assertGreater(checked, 0, 'seed 里没有任何项目图 —— 本守卫失去被测对象')
        self.assertEqual(
            offenders, [],
            '以下项目图 alt 未包含项目真实名称（很可能又退化成 slug 人性化文本）：'
            f'{offenders}')

    def test_seed_project_gallery_alt_subject_is_the_real_title(self):
        """alt 的形态契约：主体段（首个「 — 」之前）必须 == 项目真名，且带地点。

        被清空的旧写法是 ``"Football Field LED Retrofit — view 1"`` —— 主体取自
        slug 分词，实体名 "Bohemia Manor High School" 和地点 "United States"
        双双丢失。

        ⚠️ **不能用** ``slug.replace('-', ' ').title()`` 做黑名单判据，两个原因：

        1. 22 个项目里有 11 个的 ``title`` **本身就等于** slug 人性化
           （`nanshan-ski-village` → "Nanshan Ski Village"、
           `beijing-international-tennis-center` → "Beijing International Tennis
           Center"），黑名单会把正确的 alt 全判违规 —— 实测误报 52 条。
        2. slug 里的 ``led`` 分词 title-case 后是 "Led"，而真实旧文案写的是
           "LED"，``startswith`` 判据**连真病灶都抓不到**。

        所以改用正向契约（主体 == title），既零误报又能抓住真退化。
        """
        bad_subject = []
        bad_location = []
        for d in _load_seed().get('projects', []):
            slug = d.get('slug', '')
            dp = _DictProject(d)
            _enrich_project(dp, 'en')
            title = (d.get('title') or '').strip()
            location = (getattr(dp, 'location_t', '') or '').strip()
            for g in (dp.gallery or []):
                alt = g.get('alt') or ''
                subject = alt.split(' \u2014 ', 1)[0].strip()
                if subject != title:
                    bad_subject.append((slug, title, alt))
                if location and location not in alt:
                    bad_location.append((slug, location, alt))
        self.assertEqual(
            bad_subject, [],
            '以下项目图 alt 的主体段不是项目真名（很可能又退化成 slug 分词）：'
            f'{bad_subject}')
        self.assertEqual(
            bad_location, [],
            '以下项目图 alt 丢了地点（项目有 location 却没写进 alt）：'
            f'{bad_location}')


class ProjectAltDatabaseSyncTests(SimpleTestCase):
    """DB 侧不得存在会让本地 alt 偏离生产的 override。

    🔴 读真实 `db.sqlite3`（只读），不用 ORM —— 测试库是空的。
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.exists(DB_PATH):
            raise cls.skipTest(
                'db.sqlite3 不存在（生产为无状态部署）—— 本守卫只适用于本地开发环境')
        cls._con = sqlite3.connect(
            'file:%s?mode=ro' % DB_PATH.replace('\\', '/'), uri=True)
        cls.rows = cls._con.execute(
            "select p.slug, i.alt_text from pages_projectimage i "
            "join pages_project p on p.id = i.project_id "
            "where i.alt_text is not null and i.alt_text <> '' "
            "order by p.slug"
        ).fetchall()

    @classmethod
    def tearDownClass(cls):
        try:
            cls._con.close()
        finally:
            super().tearDownClass()

    def test_no_project_image_overrides_the_auto_alt(self):
        """任何非空 `ProjectImage.alt_text` 都会让本地 alt 偏离生产。

        因为 seed 分支（生产）不读这个字段。要么留空，要么先让
        `pages/seed_sync.py` 把 alt 导出进 seed —— 不能只改一边。
        """
        self.assertEqual(
            self.rows, [],
            '以下项目图仍写死了 alt_text，本地渲染会覆盖自动生成的 '
            '"{title} — {location} — view N" 从而与生产不一致：'
            f'{self.rows}。修法：留空（推荐，与生产一致）；'
            '若确需自定义，必须先让 seed_sync 导出 alt 再写值。')
