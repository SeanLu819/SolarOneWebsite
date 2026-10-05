"""静态资源完整性守卫。

2026-09-30 修复：``get_common_context()`` 在 ``SiteConfig.hero_background`` 为空时会回退到一张
hero 首图。回退文件名必须与实际磁盘文件**逐字符一致**——之前回退到不存在的裸名
``images/hero-main.webp``，导致生产每次 GET 都打 ``no hashed static URL`` 警告并回退 404。

守卫两条不变量：
  1. 幽灵名 ``images/hero-main.webp`` 永远不许再出现在代码里；
  2. 回退目标 ``images/hero-main-1.webp`` 必须真实存在于 static/images。

2026-10-03 v1.9.9 追加：``_list_static_dir()`` 的目录枚举**只能有一个真源**
（``static/``）。把 ``STATIC_ROOT``（collectstatic 陈旧快照）合并进同一集合会让
旧文件名的哈希副本压过新上传的图 → 页面引用磁盘上不存在的文件 → 404。见
``pages/views/utils.py:_list_static_dir`` 的 docstring 与下方
``StaticDirListingSourceOfTruthTests``。

2026-10-04 v1.10.15 追加两条，同一场事故的另一半：
  3. ``enrich.invalidate_enrichment_cache()`` 必须**真的**清掉 ``utils`` 的目录列表
     缓存 —— 它此前是空操作（局部重绑定），于是 admin 上传的图在长驻 dev 进程里
     永远不生效（``ClearStaticCachesOnAdminSaveTests``）；
  4. ``_list_static_dir()`` 的 ``STATIC_ROOT`` 回退必须同样过一遍陈旧快照减法，
     与 ``_build_static_file_set()`` 对齐（``GalleryFallbackGhostTests``）。
"""
import os
import re
import tempfile

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings

_PAGES = Path(__file__).resolve().parent
_COMMON = _PAGES / 'views' / 'common.py'
_API_INDEX = _PAGES.parent / 'api' / 'index.py'
_STATIC_IMAGES = _PAGES.parent / 'static' / 'images'

HERO_FALLBACK = 'images/hero-main-1.webp'  # 必须与 common.py:67 回退名一致


class HeroFallbackImageTests(TestCase):
    def test_no_ghost_hero_main_webp_reference(self):
        """common.py / api/index.py 都不得再引用不存在的裸名 hero-main.webp。"""
        for src in (_COMMON, _API_INDEX):
            text = src.read_text(encoding='utf-8')
            self.assertNotIn(
                "'images/hero-main.webp'",
                text,
                f"{src.name} 仍引用了幽灵文件 'images/hero-main.webp'（已修复为 hero-main-1.webp）",
            )

    def test_hero_fallback_target_exists_on_disk(self):
        """回退目标 hero-main-1.webp 必须真实存在于 static/images，否则线上会 404。"""
        target = _STATIC_IMAGES / 'hero-main-1.webp'
        self.assertTrue(
            target.exists(),
            f"hero 回退目标 {target} 在 static/images 中缺失",
        )

    def test_hero_fallback_target_is_referenced_in_template(self):
        """home.html 已使用 hero-main-1.webp（含 1280/portrait 变体），回退名与之一致。"""
        home = _PAGES.parent / 'templates' / 'home.html'
        text = home.read_text(encoding='utf-8')
        self.assertIn(
            "images/hero-main-1.webp",
            text,
            "home.html 未引用 hero-main-1.webp，回退名与模板首图不一致",
        )


class StaticDirListingSourceOfTruthTests(TestCase):
    """目录枚举必须以 static/ 为唯一真源（v1.9.9，防陈旧 collectstatic 快照抢占）。

    事故现场：``static/images/projects/beijing-international-tennis-center/`` 只有
    4 张新上传的 ``bitc-tennis-court-light-720p-0{1..4}.webp``，而 ``staticfiles/``
    里躺着上一轮 collectstatic 的陈旧快照（旧图 + 它们的哈希副本
    ``bitc-tennis-01.d5801a84901f.webp``）。旧实现把两边合并进同一集合，
    精确同名分支先命中哈希副本 → 页面 8 个 ``<img>`` 全 404，新图一张不显示。
    """

    def setUp(self):
        # 目录列表是进程级缓存，不清会串到后续用例。
        from pages.views import utils
        self.utils = utils
        utils._dir_listing_cache.clear()
        self.addCleanup(utils._dir_listing_cache.clear)

    def test_listing_matches_live_static_dir_exactly(self):
        """目录在 static/ 里存在时，枚举结果必须等于该目录的真实内容。"""
        rel = 'images/projects/beijing-international-tennis-center'
        src = Path(settings.BASE_DIR) / 'static' / rel
        if not src.is_dir():
            self.skipTest(f'{rel} 不在 static/ 下，跳过')
        expected = set(os.listdir(src))
        with override_settings(DEBUG=False):  # 本地默认就是 False（settings.py:72）
            got = self.utils._list_static_dir(rel)
        self.assertEqual(
            set(got), expected,
            '目录枚举混入了 static/ 之外的文件名（陈旧 staticfiles 快照会抢占新图）',
        )

    def test_no_stale_snapshot_name_survives_exact_match(self):
        """精确同名解析不得返回只存在于 staticfiles/ 的哈希副本名。

        用真实数据回归：该 slug 的封面必须解析到 static/ 里真实存在的那一张。
        """
        rel = 'images/projects/beijing-international-tennis-center'
        src = Path(settings.BASE_DIR) / 'static' / rel
        if not src.is_dir():
            self.skipTest(f'{rel} 不在 static/ 下，跳过')
        names = os.listdir(src)
        # 只存在于 staticfiles/ 的名字（即陈旧快照独有、磁盘真源没有的）
        stale_only = {
            n for n in names
            if not (src / n).exists()
        }
        with override_settings(DEBUG=False):
            listing = self.utils._list_static_dir(rel)
        self.assertEqual(
            listing & stale_only, set(),
            f'陈旧快照独有文件名混进枚举：{sorted(listing & stale_only)[:3]}',
        )
        cover = self.utils._find_project_cover_path(
            'beijing-international-tennis-center', 'projects/bitc-tennis-01.webp')
        self.assertTrue(
            cover and (Path(settings.BASE_DIR) / 'static' / cover).exists(),
            f'封面解析到不存在的文件：{cover!r}',
        )

    def test_falls_back_to_static_root_when_source_dir_absent(self):
        """真源目录不存在时仍要回退 STATIC_ROOT —— 减法不许把回退分支整个废掉。

        🔴 v1.10.15 重写。原版拿 ``images/projects/gallery`` 当样例并断言结果非空 ——
        那时它能过，恰恰**因为**减法还没接上。v1.10.15 把陈旧快照减法补齐后，那个
        目录里的 70 个文件全是「只存在于 staticfiles/ 快照、真源没有」的幽灵，
        被正确地减成了空集，旧断言于是变红。

        旧样例证明的是「减法没生效」，不是「回退分支还在」。这里造一个减法管不着的
        情形：**真源 `STATICFILES_DIRS` 为空** ⇒ 那批文件不算陈旧快照（减法以
        「不在真源里」为判据）⇒ 回退结果应当原样保留。

        减法本身的守卫在 ``test_stale_fallback_names_are_subtracted_too``。
        """
        rel = 'images/projects/qa-fallback-probe'
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            snapshot = base / 'staticfiles' / rel
            snapshot.mkdir(parents=True)
            (snapshot / 'probe.webp').write_bytes(b'p')
            (base / 'static').mkdir()   # 真源存在但没有 rel 目录 → 触发回退
            self.utils.clear_static_caches()
            with override_settings(
                BASE_DIR=base,
                STATICFILES_DIRS=[],          # 真源一个文件都没有 ⇒ 无从减
                STATIC_ROOT=str(base / 'staticfiles'),
                DEBUG=False,
            ):
                got = self.utils._list_static_dir(rel)
            self.assertIn(
                'probe.webp', got,
                '回退 STATIC_ROOT 的分支被误删/被减法清空，生产目录枚举会退化为空',
            )
            self.utils.clear_static_caches()

    def test_find_static_ignores_stale_snapshot_only_paths(self):
        """``_find_static()`` 不得因为陈旧快照就把磁盘上不存在的文件判成 HIT。"""
        from pages.views import utils
        old = 'images/projects/beijing-international-tennis-center/bitc-tennis-01.webp'
        new = 'images/projects/beijing-international-tennis-center/' \
              'bitc-tennis-court-light-720p-01.webp'
        src = Path(settings.BASE_DIR) / 'static' / 'images/projects' \
            / 'beijing-international-tennis-center'
        if not src.is_dir():
            self.skipTest('用例依赖目录不存在，跳过')
        # 前提：旧名已从真源删除、新名真源存在（v1.9.9 事故现场）。
        self.assertFalse((src / 'bitc-tennis-01.webp').exists(), '用例前提变化：旧名又回来了')
        self.assertTrue((src / 'bitc-tennis-court-light-720p-01.webp').exists())
        self.assertFalse(
            utils._find_static(old),
            '_find_static 被陈旧 staticfiles 快照欺骗，会拼出 404 的 URL',
        )
        self.assertTrue(
            utils._find_static(new),
            '减法误伤了真源文件（真源存在却被判 MISS）',
        )

    def test_stale_fallback_names_are_subtracted_too(self):
        """🔴 v1.10.15 — STATIC_ROOT 回退也必须过陈旧快照减法。

        v1.9.9 只给 ``_build_static_file_set()`` 加了减法，``_list_static_dir()``
        这条枚举路径漏了，于是同一个「只有一个真源」原则在两个入口上表现不一致。
        现场（2026-10-04 源深体育场）：``static/images/projects/gallery`` 不存在，
        而 ``staticfiles/`` 的旧快照里有同名的 ``shys-soccer-0{1..5}.webp``
        （该项目最早就是按 ``gallery/`` 传的）。本地 ``DEBUG=False`` 让回退分支生效，
        5 张刚上传的图被解析成只存在于快照的路径 → 全 404。

        用临时目录复刻那个目录形状（真源无 ``gallery/``，快照有 5 张同名图）。
        由 ``GalleryFallbackGhostTests`` 从调用方角度断言「解析结果不许指向磁盘上
        不存在的文件」。
        """
        rel = 'images/projects/gallery'
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            snapshot = base / 'staticfiles' / rel
            snapshot.mkdir(parents=True)
            ghosts = [f'shys-soccer-0{i}.webp' for i in range(1, 6)]
            for name in ghosts:
                (snapshot / name).write_bytes(b'g')
            (base / 'static').mkdir()   # 真源存在，但没有 gallery/ 子目录
            self.utils.clear_static_caches()
            with override_settings(
                BASE_DIR=base,
                STATICFILES_DIRS=[str(base / 'static')],
                STATIC_ROOT=str(base / 'staticfiles'),
                DEBUG=False,
            ):
                listing = self.utils._list_static_dir(rel)
            self.assertTrue(ghosts, '用例前提不成立')
            self.assertEqual(
                listing & set(ghosts), set(),
                f'回退带进来的陈旧快照名没被减掉：{sorted(listing)[:3]}',
            )
            self.utils.clear_static_caches()

    def test_the_subtraction_never_drops_a_real_source_file(self):
        """🔴 v1.10.15 — 减法绝不能少报真源 `static/` 里真实存在的文件。

        变异探针实测：把减法整段去掉，全绿 —— 说明「剔幽灵」有人守、「不误伤」
        没人守。而后者才是致命方向：真源明明有图，枚举却少了它，页面会反过来
        一张都不显示（比原事故更隐蔽，因为它只在真源文件与快照重名时发作）。

        断言方式用「一个都不许少」，而不是逐个名字比对：``os.listdir(static/<rel>)``
        的每个元素都必须在枚举结果里。任何少报都会被抓到，且不依赖构造多刁钻的
        场景（真源目录存在时压根不走 ``STATIC_ROOT`` 回退，减法那半句不在判定链上，
        这一点由 ``test_listing_matches_live_static_dir_exactly`` 兜底）。

        全程用 ``tempfile`` + ``override_settings`` 重定向，不碰真实 ``static/``。
        """
        rel = 'images/projects/qa-subtraction-probe'
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / 'static' / rel
            src.mkdir(parents=True)
            names = ['a.webp', 'b.webp', 'c.webp']
            for name in names:
                (src / name).write_bytes(b'x')
            # 快照里放同名 + 独有名，减法该动的只有独有名。
            snapshot = base / 'staticfiles' / rel
            snapshot.mkdir(parents=True)
            for name in names:
                (snapshot / name).write_bytes(b'x')
            (snapshot / 'ghost.webp').write_bytes(b'g')

            self.utils.clear_static_caches()
            with override_settings(
                BASE_DIR=base,
                STATICFILES_DIRS=[str(base / 'static')],
                STATIC_ROOT=str(base / 'staticfiles'),
                DEBUG=False,
            ):
                got = self.utils._list_static_dir(rel)
            missing = sorted(set(names) - set(got))
            self.assertEqual(
                missing, [],
                '减法少报了真源 static/ 里真实存在的文件；页面会反过来一张图都不显示',
            )
            self.utils.clear_static_caches()

    def test_the_subtraction_is_a_no_op_in_the_production_shape(self):
        """🔴 v1.10.15 — 减法在 Vercel 上必须是空操作。

        生产（``IS_VERCEL``）的函数包里既没有 ``static/`` 也没有 ``staticfiles/``，
        唯一真源是构建期写出的 ``pages/static_index_data.STATIC_INDEX``。
        ``_stale_snapshot_rel_paths()`` 在那种形态下拿不到任何目录、直接返回空集，
        减法因此不裁剪任何东西。

        这条守卫是 B 改动**不伤线上**的唯一保证：如果将来有人把减法改成无条件执行
        （比如去掉 ``os.path.isdir(root)`` 提前返回），生产会丢掉索引里的全部文件，
        而本地一切正常 —— 只有这条会红。
        """
        self.utils.clear_static_caches()
        # 用空 STATICFILES_DIRS / 不存在的 STATIC_ROOT 模拟函数包形态。
        with override_settings(STATICFILES_DIRS=(), STATIC_ROOT='/nonexistent-probe'):
            self.assertEqual(
                self.utils._stale_snapshot_rel_paths(), set(),
                '生产形态下减法本该是空集；非空说明它会裁剪构建期索引',
            )
            # 索引里有的目录必须原样枚举出来，一项都不能少。
            indexed = [
                rel for rel, names in
                (self.utils._load_static_index().get('dirs') or {}).items()
                if names and rel.startswith('images/projects/')
            ]
            if not indexed:
                self.skipTest('本地没有 static_index_data.py（生产形态由构建生成）')
            rel = indexed[0]
            self.utils.clear_static_caches()
            self.assertEqual(
                set(self.utils._index_dir_listing(rel)),
                set(self.utils._list_static_dir(rel)),
                f'生产形态下 {rel} 的索引条目被减法裁掉了',
            )


class ClearStaticCachesOnAdminSaveTests(SimpleTestCase):
    """🔴 v1.10.15 — ``invalidate_enrichment_cache()`` 曾经是**空操作**。

    原实现：

        from .utils import _dir_listing_cache, _static_file_set
        _dir_listing_cache = {}      # ← 局部重绑定，utils 里的字典纹丝不动
        _static_file_set = None      # ← 同上

    ``from ... import`` 只把名字绑进函数局部作用域，所以这两行新建的是局部对象。
    上面四个 ``_enriched_*_cache`` 因为有 ``global`` 声明而是真的清了 —— 不对称
    正是它长期潜伏的原因：测试进程每次都是空缓存，谁也看不出来。

    只有**长驻进程**会显形，这正是 dev server：早于 admin 上传的那次请求把
    ``images/projects/<slug>/`` 缓存成空集，上传后 post_save 触发的失效又是空操作，
    空集继续命中 → 新图一张不显示。
    """

    def setUp(self):
        from pages.views import utils
        self.utils = utils
        utils.clear_static_caches()
        self.addCleanup(utils.clear_static_caches)

    def test_it_really_flushes_the_directory_listing_cache(self):
        """断言的是 utils 的字典本身，不是某个副本。"""
        self.utils._dir_listing_cache.clear()
        self.utils._dir_listing_cache['probe/key'] = {'x'}
        original = id(self.utils._dir_listing_cache)

        from pages.views.enrich import invalidate_enrichment_cache
        invalidate_enrichment_cache()

        self.assertNotIn(
            'probe/key', self.utils._dir_listing_cache,
            'invalidate_enrichment_cache() 没有清掉 utils 的目录列表缓存'
            '（局部重绑定，不是真失效）',
        )
        self.assertEqual(
            id(self.utils._dir_listing_cache), original,
            '实现改成了重新绑定新字典；已持有引用的调用方会看不到失效',
        )

    def test_it_flushes_every_static_lookup_cache(self):
        """`_static_file_set` / `_static_index` / 陈旧快照减法结果都得重算。

        后两个是 v1.10.15 一并接进 `clear_static_caches()` 的：磁盘上的文件集合变了，
        减法结果和构建期索引都得重新读。
        """
        self.utils._static_file_set = {'STALE'}
        self.utils._static_index = {'dirs': {'probe': ['x']}}
        self.utils._stale_snapshot_cache = {'STALE'}
        self.utils._PRODUCT_DIR_IMAGE_CACHE['probe'] = 1

        from pages.views.enrich import invalidate_enrichment_cache
        invalidate_enrichment_cache()

        self.assertIsNone(self.utils._static_file_set,
                          '_static_file_set 没被清（新增/删除的静态文件不会被感知）')
        self.assertIsNone(self.utils._static_index,
                          '_static_index 没被清（构建期索引与磁盘已不一致）')
        self.assertIsNone(self.utils._stale_snapshot_cache,
                          '陈旧快照减法结果被缓存了，文件搬走后减法就不准了')
        self.assertEqual(self.utils._PRODUCT_DIR_IMAGE_CACHE, {},
                         '产品目录图缓存没被清')

    def test_clear_static_caches_mutates_in_place(self):
        """`.clear()` 而不是重新绑定 —— 持有引用的调用方必须看得到失效。"""
        self.utils._dir_listing_cache['probe/key'] = {'x'}
        original = id(self.utils._dir_listing_cache)
        self.utils.clear_static_caches()
        self.assertEqual(id(self.utils._dir_listing_cache), original)
        self.assertNotIn('probe/key', self.utils._dir_listing_cache)


class GalleryFallbackGhostTests(TestCase):
    """🔴 v1.10.15 — 项目页引用的每一张图都必须真实存在于 ``static/``。

    这是本次事故的端到端不变量。上面两条守卫分别锁住「缓存会被清」和「回退会减」，
    但它们都是间接的：即使其中一条退化，只要另一条还在，页面仍可能 404 或不显示。

    这里从**调用方**角度断言最终 URL —— 整站所有项目的每一个 gallery URL 都过一遍
    磁盘存在性。真实数据回归（``yuanshen-sports-centre-stadium`` 的 5 张图），
    不用构造 fixture，因此任何人把图改名、搬目录或只传到 media/ 都会被立刻抓住。
    """

    def _seed_projects(self):
        from pages.views.data_loaders import _load_seed
        return [p for p in _load_seed().get('projects', []) if p.get('slug')]

    def test_no_project_gallery_url_points_at_a_missing_file(self):
        from pages.views import utils
        utils.clear_static_caches()
        projects = self._seed_projects()
        self.assertTrue(projects, 'seed 里没有项目，用例无从验证')
        missing = []
        total = 0
        for project in projects:
            for url in utils._project_gallery_urls(project['slug']):
                total += 1
                rel = url.replace('/static/', '', 1)
                if not (Path(settings.BASE_DIR) / 'static' / rel).exists():
                    missing.append(f'{project["slug"]}: {rel}')
        self.assertEqual(
            missing, [],
            '项目页引用了 static/ 下不存在的图（多为只存在于 collectstatic '
            f'快照的名字）: {missing[:5]}',
        )
        self.assertGreater(total, 0, '没有任何 gallery URL，用例空通过')

    def test_a_new_gallery_image_on_existing_project_is_visible(self):
        """C-1 守卫：给**已有**项目加新图，必须让 ProjectImage 的 post_save 失效缓存。

        这正是 2026-10-04 的现场：用户在后台给已存在的源深项目重新传了 5 张图，
        但早于上传那次请求把目录缓存成了空集，上传后缓存没被清 → 新图解析不出。

        🔴 时序隔离（变异探针抓出来的坑）：必须先建好 Project、再让「上传前的请求」
        把目录缓存成空集、最后才存 ProjectImage。这样 Project 的 post_save（C-2）
        发生在缓存填充**之前**，不会替 C-1 兜底。若 C-1 的 ``_invalidate_views_cache()``
        被删，缓存里的空集继续命中 → 新图解析不出 → 本用例红。

        ``MEDIA_ROOT`` **不**重定向（曾因 ``override_settings(MEDIA_ROOT=...)`` 把
        整份测试从 ~40s 拖到 706s）；``media/`` 在 gitignore 里，写真实目录无害。
        """
        from pages.models import Project, ProjectImage
        from pages.views import utils

        slug = 'qa-ghost-upload'
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            static_root = base / 'static'
            slug_dir = static_root / 'images' / 'projects' / slug
            media_dir = Path(settings.MEDIA_ROOT) / 'projects'
            media_dir.mkdir(parents=True, exist_ok=True)
            self.addCleanup(utils.clear_static_caches)

            probe = media_dir / 'ghost-probe.webp'
            probe.write_bytes(b'fake-webp-bytes')
            with override_settings(
                BASE_DIR=base,
                STATICFILES_DIRS=[str(static_root)],
                STATIC_ROOT=str(base / 'staticfiles'),
                DEBUG=False,
            ):
                # 1. 已有项目（其 post_save 在缓存填充之前触发，不兜底）。
                project = Project.objects.create(
                    title='QA Ghost Upload', slug=slug, order=999)
                # 2. 上传前的请求把目录缓存成空集。
                utils.clear_static_caches()
                self.assertEqual(utils._project_gallery_urls(slug), [],
                                 '用例前提：上传前目录应缓存为空')
                # 3. admin 上传新图 —— 只有 ProjectImage 的 post_save 会触发。
                row = ProjectImage.objects.create(
                    project=project,
                    image='projects/ghost-probe.webp',
                    order=0,
                )
                self.assertTrue(
                    (slug_dir / 'ghost-probe.webp').exists(),
                    'media→static 同步没产出文件，测的不是缓存失效')
                # 4. 没失效则空集继续命中 → 404。
                urls = utils._project_gallery_urls(slug)
                self.assertTrue(
                    any('ghost-probe' in u for u in urls),
                    '给已有项目加的新图不可见 —— ProjectImage post_save 没失效缓存'
                    f'（解析结果 {urls}）')
            utils.clear_static_caches()
            # os.remove 而非 Path.unlink()：批量删除计数到阈值后 shell 层的删除会
            # 被安全策略拦下挂起（实测 40s 拖到 >13min）。
            if probe.exists():
                os.remove(probe)
            project.delete()  # 级联删 ProjectImage

    def test_a_new_project_cover_is_visible_after_save(self):
        """C-2 守卫：新建带封面的项目，Project 的 post_save 必须失效缓存。

        与 C-1 对称：先让「项目还不存在时」的请求把目录缓存成空集，再创建带封面的
        Project —— 这时只有 C-2 会失效。若 C-2 的 ``_invalidate_views_cache()`` 被删，
        缓存里的空集继续命中，封面解析不出 → 本用例红。

        ``MEDIA_ROOT`` 不重定向（见 C-1 注释）。
        """
        from pages.models import Project
        from pages.views import utils

        slug = 'qa-ghost-cover'
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            static_root = base / 'static'
            media_dir = Path(settings.MEDIA_ROOT) / 'projects'
            media_dir.mkdir(parents=True, exist_ok=True)
            self.addCleanup(utils.clear_static_caches)

            probe = media_dir / 'ghost-cover.webp'
            probe.write_bytes(b'fake-webp-bytes')
            with override_settings(
                BASE_DIR=base,
                STATICFILES_DIRS=[str(static_root)],
                STATIC_ROOT=str(base / 'staticfiles'),
                DEBUG=False,
            ):
                # 1. 项目还不存在时的请求把目录缓存成空集。
                utils.clear_static_caches()
                self.assertEqual(utils._project_gallery_urls(slug), [],
                                 '用例前提：项目创建前目录应缓存为空')
                # 2. admin 创建带封面的项目 —— C-2（Project post_save）同步 + 失效。
                project = Project.objects.create(
                    title='QA Cover', slug=slug, order=999,
                    image='projects/ghost-cover.webp')
                cover = utils._find_project_cover_path(slug)
                self.assertTrue(
                    cover and 'ghost-cover' in cover,
                    '新建项目封面不可见 —— Project post_save 没失效缓存'
                    f'（解析结果 {cover!r}）')
            utils.clear_static_caches()
            if probe.exists():
                os.remove(probe)
            project.delete()


class CoverImageFromGalleryTests(TestCase):
    """🔴 v1.10.15 封面机制 — 「从轮播图选封面」必须复用轮播图文件，不另存。

    新增 ``cover_image`` 外键（Project→ProjectImage / Product→ProductImage）。
    解析优先级：cover_image → image → 第一张轮播图。选中轮播图当封面时，
    image_url 必须指向该轮播图文件（同一份静态资源），不得再指向一个独立
    上传的 image 文件（那才是重复保存、占空间的根因）。

    守卫两条不变量：
      1. cover_image 指向某张轮播图、image 留空时，image_url 命中该轮播图文件；
      2. cover_image 与独立 image 同时存在时，cover_image 优先（image 被忽略）。
    """

    def _write_static(self, slug_dir, name):
        slug_dir.mkdir(parents=True, exist_ok=True)
        (slug_dir / name).write_bytes(b'fake-webp-bytes')

    def test_product_cover_reuses_gallery_file(self):
        from pages.models import Product, ProductImage
        from pages.views import utils
        from pages.views.utils import _db_product_cover_url

        slug = 'qa-cover-prod'
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            static_root = base / 'static'
            slug_dir = static_root / 'images' / 'products' / slug
            media_dir = Path(settings.MEDIA_ROOT) / 'products'
            media_dir.mkdir(parents=True, exist_ok=True)
            self.addCleanup(utils.clear_static_caches)
            probe = media_dir / 'qa-cover-gallery.webp'
            probe.write_bytes(b'fake-webp-bytes')

            with override_settings(
                BASE_DIR=base,
                STATICFILES_DIRS=[str(static_root)],
                STATIC_ROOT=str(base / 'staticfiles'),
                DEBUG=False,
            ):
                product = Product.objects.create(
                    name='QA Cover Prod', slug=slug, category='FLOODLIGHT',
                    description='QA', image='')
                gallery = ProductImage.objects.create(
                    product=product,
                    image='products/gallery/qa-cover-gallery_x7aB9cD.webp',
                    order=0)
                product.cover_image = gallery
                product.save(update_fields=['cover_image'])
                self._write_static(slug_dir, 'qa-cover-gallery.webp')

                url = _db_product_cover_url(product)
                self.assertTrue(
                    url and 'qa-cover-gallery' in url,
                    f'封面未复用轮播图文件，image_url={url!r}')
                # 🔴 delete() 必须在 override_settings 块**内**。
                # post_delete → sync_product_on_save 会 os.makedirs(
                # BASE_DIR/static/images/products/<slug>)：出了块 BASE_DIR
                # 恢复真值，就会在真实 static/ 里凭空造出空目录，
                # 并把 tests_cert_images 的空目录守卫拉红（已踩）。
                utils.clear_static_caches()
                product.delete()
            utils.clear_static_caches()
            if probe.exists():
                os.remove(probe)

    def test_product_cover_wins_over_separate_image(self):
        from pages.models import Product, ProductImage
        from pages.views import utils
        from pages.views.utils import _db_product_cover_url

        slug = 'qa-cover-prod2'
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            static_root = base / 'static'
            slug_dir = static_root / 'images' / 'products' / slug
            media_dir = Path(settings.MEDIA_ROOT) / 'products'
            media_dir.mkdir(parents=True, exist_ok=True)
            self.addCleanup(utils.clear_static_caches)
            probe = media_dir / 'qa-cover-gallery.webp'
            probe.write_bytes(b'fake-webp-bytes')

            with override_settings(
                BASE_DIR=base,
                STATICFILES_DIRS=[str(static_root)],
                STATIC_ROOT=str(base / 'staticfiles'),
                DEBUG=False,
            ):
                product = Product.objects.create(
                    name='QA Cover Prod2', slug=slug, category='FLOODLIGHT',
                    description='QA',
                    image='products/qa-cover-separate_x1aB2cD.webp')
                gallery = ProductImage.objects.create(
                    product=product,
                    image='products/gallery/qa-cover-gallery_x7aB9cD.webp',
                    order=0)
                product.cover_image = gallery
                product.save(update_fields=['cover_image'])
                self._write_static(slug_dir, 'qa-cover-gallery.webp')
                self._write_static(slug_dir, 'qa-cover-separate.webp')

                url = _db_product_cover_url(product)
                self.assertTrue(
                    url and 'qa-cover-gallery' in url,
                    f'封面应优先选中的轮播图，image_url={url!r}')
                self.assertNotIn(
                    'qa-cover-separate', url or '',
                    f'封面不该落到独立主图文件（重复保存），image_url={url!r}')
                # 🔴 delete() 必须在 override_settings 块内，理由见上一条。
                utils.clear_static_caches()
                product.delete()
            utils.clear_static_caches()
            if probe.exists():
                os.remove(probe)

    def test_project_cover_reuses_gallery_file(self):
        from pages.models import Project, ProjectImage
        from pages.views import utils
        from pages.views.utils import _db_project_cover_url

        slug = 'qa-cover-proj'
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            static_root = base / 'static'
            slug_dir = static_root / 'images' / 'projects' / slug
            media_dir = Path(settings.MEDIA_ROOT) / 'projects'
            media_dir.mkdir(parents=True, exist_ok=True)
            self.addCleanup(utils.clear_static_caches)
            probe = media_dir / 'qa-cover-gallery.webp'
            probe.write_bytes(b'fake-webp-bytes')

            with override_settings(
                BASE_DIR=base,
                STATICFILES_DIRS=[str(static_root)],
                STATIC_ROOT=str(base / 'staticfiles'),
                DEBUG=False,
            ):
                project = Project.objects.create(
                    title='QA Cover Proj', slug=slug, location='QA',
                    description='QA', image='')
                gallery = ProjectImage.objects.create(
                    project=project,
                    image='projects/gallery/qa-cover-gallery_x7aB9cD.webp',
                    order=0)
                project.cover_image = gallery
                project.save(update_fields=['cover_image'])
                self._write_static(slug_dir, 'qa-cover-gallery.webp')

                url = _db_project_cover_url(project)
                self.assertTrue(
                    url and 'qa-cover-gallery' in url,
                    f'项目封面未复用轮播图文件，image_url={url!r}')
                # 🔴 delete() 必须在 override_settings 块内，理由见产品那条。
                utils.clear_static_caches()
                project.delete()
            utils.clear_static_caches()
            if probe.exists():
                os.remove(probe)


class HeroDeferredSlideLoadingTests(TestCase):
    """首页 hero 第 2/3 张必须走 data-src 延迟加载（v1.10.1）。

    ``.hero-slide`` 是 ``position:absolute; inset:0`` —— 元素永远在视口内，
    只靠 ``opacity:0`` 隐藏。于是 ``loading="lazy"`` 对它们**完全无效**：
    首屏一次就下载三张全屏图（实测 541.9KB，其中 86% 首屏不可见）。
    本组守卫把「第 2/3 张不得有裸 src」和「轮播必须真的补上 src」焊死，
    防止有人手滑把 src 写回去把 lazy 的谎圆上。
    """

    @classmethod
    def setUpTestData(cls):
        # -*- coding: utf-8 无关；模板里是 ASCII 属性名 + 中文字典常量
        cls.home = Path(settings.BASE_DIR, 'templates', 'home.html'
                        ).read_text(encoding='utf-8')
        cls.base = Path(settings.BASE_DIR, 'templates', 'base.html'
                        ).read_text(encoding='utf-8')
        cls.css = Path(settings.BASE_DIR, 'static', 'css', 'base.css'
                       ).read_text(encoding='utf-8')

    def _pictures(self):
        return re.findall(r'<picture>.*?</picture>', self.home, re.DOTALL)

    def _attrs(self, snippet):
        return (re.findall(r'<source[^>]*>', snippet) or [''])[0], \
            (re.findall(r'<img[^>]*>', snippet) or [''])[0]

    @staticmethod
    def _has_real_attr(pattern, text):
        """``\\s`` 前缀必须保留：``data-src="`` 里含子串 ``src="``，
        裸 assertNotIn 会把每个延迟属性都误判成裸属性。"""
        return re.search(pattern, text) is not None

    def test_home_hero_has_three_pictures(self):
        self.assertEqual(len(self._pictures()), 3,
                         'hero 图片结构变了，本组用例需复核')

    def test_slide_one_keeps_a_real_src_for_the_lcp_image(self):
        # 首图是 LCP：不能延迟，否则无 JS 时首屏空白
        _, img = self._attrs(self._pictures()[0])
        self.assertTrue(self._has_real_attr(r'\ssrc="', img),
                        '首图不再是静态 src，无 JS 时首屏会空白')
        self.assertIn('hero-slide active', img, '首图丢了 active 类')
        self.assertIn('fetchpriority="high"', img, '首图丢了 fetchpriority')

    def test_slides_two_and_three_are_deferred(self):
        for idx, pic in enumerate(self._pictures()[1:], start=2):
            source, img = self._attrs(pic)
            # 真实 src/srcset 会让浏览器立刻下载；\s 前缀保证只命中裸属性，
            # 不被 data-src= / data-srcset= 骗到
            self.assertFalse(self._has_real_attr(r'\ssrc="', img),
                             f'hero-{idx} 又写了裸 src，首屏预算白省')
            self.assertFalse(self._has_real_attr(r'\ssrcset="', img),
                             f'hero-{idx} 又写了裸 srcset，首屏预算白省')
            self.assertIn('data-src=', img,
                          f'hero-{idx} 没有 data-src，轮播无从取值')
            self.assertIn('data-srcset=', img,
                          f'hero-{idx} 缺 data-srcset（桌面分档会退化成 1920w）')
            # 竖版 <source> 同样是下载入口，漏延迟 = 手机端仍然一进页面就下载
            self.assertIn('data-srcset=', source,
                          f'hero-{idx} 的竖版 <source> 未改为 data-srcset')
            self.assertFalse(self._has_real_attr(r'\ssrcset="', source),
                             f'hero-{idx} 的竖版 <source> 仍在立即下载')
            # 旧的失效写法不许复活
            self.assertNotIn('loading="lazy"', img,
                             f'hero-{idx} 的 loading=lazy 对 absolute 元素无效，'
                             f'应改 data-src')

    def test_carousel_restores_src_before_it_hides_the_slide(self):
        js = self.base
        self.assertIn('function ensureLoaded', js, '轮播不再补 src')
        self.assertIn("setAttribute('src'", js, 'ensureLoaded 没给 img 赋值')
        # 顺序铁律：<source> 的竖版 srcset 必须先就位，否则手机端跳过 3:4 裁剪
        self.assertLess(
            js.find("source[data-srcset]"), js.find("setAttribute('src'"),
            '轮播先给 <img> 赋 src 再补 <source>，手机端会跳过竖版裁剪',
        )
        self.assertIn('requestIdleCallback', js,
                      '缺少下一帧预热，切帧时会淡入一张空图')

    def test_hidden_inactive_slides_cannot_flash_alt_text(self):
        self.assertIn('.hero-slide:not(.active)', self.css,
                      '缺 visibility 兜底，未加载帧可能露出 alt 文本')
