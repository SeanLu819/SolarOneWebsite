# P2 — 图片外置到对象存储（根治「5 分钟构建」）

> 状态：方案已定稿，**暂缓执行**（用户决定先处理其他紧急项，图片外置后续再立项）
> 关联：`docs/seo-growth-plan.md` 的 P2「根治 5 分钟构建」
> 前置：P1 构建健壮性修复（django 钉版本 + polib 编译 .mo）已提交 `65f60cf`

---

## 1. 目标与收益（基于实测，非估算）

| 指标 | 现状 | 外置后 |
|---|---|---|
| 图片源体积（git 跟踪） | `static/images/` **42 MB / 337 文件** | 不变（可选 Phase 2 再瘦身） |
| 构建产物 `public/static/` | **138 MB**（collectstatic 同时保留哈希名+原名两份） | **≈11 MB**（仅 css/js/fonts/files + 根级小图） |
| collectstatic 处理文件数 | 1371（含 337 图片的哈希+原名双份） | ≈110（图片不再进 collectstatic） |
| CDN 上传体量（每次部署） | 138 MB（缓存未命中时分钟级） | ≈11 MB（秒级） |
| 仓库 clone 体量 | 含 42 MB 图片（历史更重） | Phase 1 不变；Phase 2 可选瘦身 |

### 访问速度影响（澄清）
**外置只治构建/部署速度，对访客访问速度中性**——这是本方案的前提，写清以免误读：
- 图片本就由 Vercel 边缘 CDN 直出；外置只是把这批文件从 Vercel CDN 换到 Cloudflare CDN（同级全球边缘网），单图延迟相当。
- 外置**不减小图片体积**、**不改善首屏/LCP**——图片该多大还是多大。真正让访客打开更快的是 **B2 批次**（CSS 异步化、字体子集、hero 懒加载、srcset 三档变体），与外置正交、互不替代。
- 唯一微小代价：独立主机 `cdn.solaronelighting.com` 的首张图片需一次额外 DNS+TLS 握手（约 1 个 RTT）。已由 Step 2 的 `<link rel="preconnect">` + `<link rel="dns-prefetch">` 抵消，运行时零额外开销。

**结论**：5 分钟不是 `build.sh` 慢（旧流程 build.sh 仅 ~7s），而是 **Vercel 缓存未命中时整包 138MB 静态产物重新上传 CDN**。外置图片把构建产物从 138MB 砍到 11MB，上传从分钟级掉到秒级——这是唯一能根治的杠杆。P1 的 `5ebf767`（去冗余 gzip + 砍 142MB 拷贝）削的是 build.sh 内的冗余，治不了上传地板；P2 治这个地板。

---

## 2. 选型：为什么 Cloudflare R2

| 候选 | 出口费 | 与现状契合 | 结论 |
|---|---|---|---|
| **Cloudflare R2** | **零出口费**（经 Cloudflare CDN 直出） | 站点 DNS/Email Routing/WAF 已在 CF，域名 `solaronelighting.com` 已 Orange-cloud | ✅ 首选 |
| Supabase Storage | 有出口费（免费额度有限） | 若后续做 J1 表单持久化可复用同一账号 | 备选（顺带解决 B6） |
| Vercel Blob | 有出口费（Pro 含额度） | 与 Vercel 同栈但需另配 | 不优先 |

**方案**：R2 桶 `solarone-static`，经 Cloudflare CDN 以 `https://cdn.solaronelighting.com` 自定义域名（Orange-cloud 子域）对外；S3 兼容协议，构建用 `boto3` 或 `aws s3 sync` 上传。零出口费 + 全球 CDN，与现有 CF 栈零新增供应商。

---

## 3. 架构总览

```
今日：  模板/解析器 → static('images/products/fl1m/fl1m-01.webp')
                       → /static/images/products/...  → Vercel CDN（public/static/，138MB）

外置后：模板/解析器 → _asset_url('images/products/fl1m/fl1m-01.webp')
                       → 若属外置集合 → https://cdn.solaronelighting.com/images/products/fl1m/fl1m-01.webp
                       → 否则 → static(...)（Vercel 本域，11MB）
```

**单点拦截**是核心：`pages/views/utils.py` 里所有图片 URL 都收口在 `static()` 与几个 helper（`_first_static` / `_static_url` / `_dict_product_image_url` / `_product_image_url` / `_project_image_url` / `_project_gallery_urls`）。新增一个 `_asset_url(rel)` 决定「外置集合→R2，其余→static()」，替换上述 helper 里的 `static()` 调用即可，**模板与 `seed_data.json` 零改动**。

---

## 4. 影响面分析（已实测）

### 4.1 外置集合（312 文件，占字节绝大多数）
- `images/products/`（193）、`images/projects/`（110）、`images/news/`（3）、`images/products_page/`（6）
- **全部经解析器输出，无 `{% static %}` 模板直引**（已 grep 确认：`templates/` 里仅 `products-bar-dark/light.webp` 是直引，且那是根级图、不在外置集合）。

### 4.2 保留本地（不经 R2）
- `static/css/`、`static/fonts/`、`static/files/`（共 ~11 MB，构成外置后的全部构建产物）
- `static/images/` 根级小图：`favicon.webp`、`apple-touch-icon.png`、`logo.webp`、`pwa-icon-192/512.png`、`hero-main-*.webp`、`home-products/about-main/optics-*/agent-*/products-bar-*`（25 文件，经 `{% static %}` 或 `config.logo_url` 直引，留本域免改模板）

### 4.3 代码收口点（精准定位）
- `pages/views/utils.py`：`_first_static`（line 143 `static(c)`）、`_static_url`（line 208 `static(rel)`）、`_dict_product_image_url`（line 250 `static(rel)`）、`_project_image_url`（line 439/442 两处 `static(...)`）→ 共 5 处改为 `_asset_url(...)`。
- `pages/storage.py` / `pages/static_index.py`：**不改**（只服务本域小资源）。
- `templates/*.html` / `seed_data.json`：**不改**。

---

## 5. 实施步骤

### Step 1 — R2 + Cloudflare 域名（你做，~0.5h）
1. Cloudflare 控制台建 R2 桶 `solaronelighting.com-static`（或 `solarone-static`）。
2. 开启「Public development」或绑定自定义域：建 `cdn.solaronelighting.com` CNAME → R2，Orange-cloud 开启（走 CF CDN，零出口费）。
3. 生成 R2 API 令牌（S3 兼容：`R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY`）。
4. 在 Vercel 配环境变量（**切勿进仓库**）：`R2_STATIC_BASE_URL=https://cdn.solaronelighting.com`、`R2_ACCOUNT_ID`、`R2_ACCESS_KEY_ID`、`R2_SECRET_ACCESS_KEY`。

### Step 2 — 代码层 `_asset_url` 拦截（~0.5d）
`pages/views/utils.py` 顶部：
```python
import os
_R2_IMAGE_PREFIXES = ('images/products/', 'images/projects/', 'images/news/', 'images/products_page/')
_R2_STATIC_BASE_URL = (os.environ.get('R2_STATIC_BASE_URL') or '').rstrip('/')

def _asset_url(rel):
    rel = (rel or '').replace('\\', '/').lstrip('/')
    if _R2_STATIC_BASE_URL and rel.startswith(_R2_IMAGE_PREFIXES):
        return f'{_R2_STATIC_BASE_URL}/{rel}'
    return static(rel)   # 其余（含根级小图）仍走 Vercel 本域
```
替换 §4.3 列出的 5 处 `static(...)` 为 `_asset_url(...)`。

`templates/base.html` head 增加预连接（R2 是独立主机，降低首图/首屏 LCP 的 DNS+TLS 开销）：
```html
<link rel="preconnect" href="https://cdn.solaronelighting.com" crossorigin>
<link rel="dns-prefetch" href="https://cdn.solaronelighting.com">
```
> 熔断开关：`R2_STATIC_BASE_URL` 为空 → `_asset_url` 全部回退 `static()`，图片瞬间回到 Vercel 本域。这是一行环境变量级 kill-switch，无需改代码。

### Step 3 — 构建上传 + 排除出 collectstatic（~0.5d）
`build.sh` 在 `seed_sync` 之后、`collectstatic` 之前插入：
1. **上传**：`aws s3 sync static/images/{products,projects,news,products_page} s3://$R2_BUCKET/ --size-only`（仅增量，快）。若 `R2_STATIC_BASE_URL` 未设则跳过（本地 `verify_static_build.py` 不受影响）。
2. **生成 R2 键清单**：扫描上述 4 目录，写 `pages/r2_index_data.py`（`R2_KEYS = {相对路径集合}`，git-ignored，与 `static_index_data.py` 同约定）。
3. **排除出 collectstatic**：构建期把 4 个目录 `mv` 到 `/tmp` 暂存 → `collectstatic` → 移回（Vercel 临时文件系统，无 git 影响；本地 `verify_static_build.py` 同步处理）。这样 `public/static/` 不再含图片 → 产物 ~11MB。

`pages/views/utils.py` 的 `_find_static` / `_list_static_dir` 对 `_R2_IMAGE_PREFIXES` 路径改查 `R2_KEYS`（prod 用，本地仍走磁盘扫描）。

### Step 4 — 守卫测试（~0.5d）
- `pages/tests_p2.py`：
  - `_asset_url('images/products/fl1m/fl1m-01.webp')` 在 `R2_STATIC_BASE_URL` 设时返回 R2 URL；未设时返回 `static(...)`。
  - `images/favicon.webp`（根级）始终返回 `static(...)`（不被外置）。
  - **构建期 fail-closed 守卫**：seed 引用的所有 bulk 图片（`product.image/banner_image/dimension_image/beam_angle_image/ordering_image/cert_image/gallery[]`、`project.image/gallery[]`、`news` 图）必须全部出现在 `R2_KEYS`，否则构建失败（沿用 `static_index --require-manifest` 哲学）。

### Step 5 — 验证与上线
- 本地：`python scripts/verify_static_build.py` 通过；`manage.py test pages.tests_p2` 全绿。
- 推送 → Vercel 部署 → `python scripts/e2e/smoke_online.py` 确认所有产品/项目/新闻图 200（域名变为 `cdn.solaronelighting.com`）。
- 复核构建日志：`public/static/` 文件数应从 1371 降到 ~110，构建产物上传明显变小。

---

## 6. 回滚 / 熔断
- **即时回滚**：Vercel 删 `R2_STATIC_BASE_URL` 环境变量 → 全站图片回到 Vercel 本域（代码无需回滚）。
- **代码回滚**：`git revert` Step 2/3 提交即可。
- **R2 数据安全**：R2 桶为追加式，误删单图可重传；建议开 R2 版本控制（可选的 30 天保留）。

---

## 7. 风险清单
| 风险 | 缓解 |
|---|---|
| R2 公共可读配置错误 → 图片 403 | 先用一张测试图 curl 验证公开可读，再全量 |
| 自定义域 SSL（CF 免费）未及时生效 | 提前建 CNAME 并等证书下发 |
| 构建期 `aws`/`boto3` 缺失 | `requirements.txt` 加 `boto3`；本地用 venv 验证 |
| 凭证泄露 | 只进 Vercel 环境变量，绝不在 repo / `seed_data` / 日志打印 |
| LCP 受独立主机影响 | `preconnect` + `dns-prefetch`；R2 经 CF CDN TTFB 全球优 |
| `_asset_url` 改漏导致部分图仍走 Vercel | 守卫测试断言外置集合前缀全覆盖 + smoke 巡检域名 |

---

## 8. 工作量估算
| 阶段 | 谁 | 耗时 |
|---|---|---|
| Step 1 R2 + CF 域名 | 你（控制台） | 0.5h |
| Step 2 代码拦截 + preconnect | AI | 0.5d |
| Step 3 构建上传 + 排除 | AI | 0.5d |
| Step 4 守卫测试 | AI | 0.5d |
| Step 5 验证上线 | 你 + AI | 0.5d |
| **合计** | | **~2–3 人日** |

---

## 9. Phase 2（可选，低优先）—— 仓库瘦身
Phase 1 已解决构建速度，但 `static/images/` 的 42MB 仍留在 git（clone 一次性承担）。若要进一步瘦身：
1. **先备份**：`tar czf ../solarone-images-$(date +%F).tgz static/images/{products,projects,news,products_page}`（放仓库外）。
2. **剔除跟踪**（用项目许可的 `git update-index --force-remove`，**禁用 `git rm`**）：`git ls-files static/images/{products,projects,news,products_page} | xargs git update-index --force-remove`。
3. `.gitignore` 追加 4 个目录。
4. 此时 Vercel 已无这些文件 → **Step 3 的构建上传必须改为从本地磁盘手动/脚本上传**（Phase 1 是每次部署 `s3 sync` 从 repo；Phase 2 后 repo 无图，需手动管理增删）。
5. 历史 blob 瘦身需 `git filter-repo`/`bfg`（重写历史，需团队协调）——更低优先，可不做。

> 建议：Phase 1 上线稳定运行 1–2 周后再决定是否做 Phase 2。绝大多数收益在 Phase 1。

---

## 10. 与 P1 的关系
- P1（`65f60cf`）是**部署健壮性**修复，与 P2 无冲突，应一起 push。
- P2 不改 `storage.py`/`static_index.py`，不与 P1 的 `ManifestStaticFilesStorage` 改动重叠。
- 执行顺序建议：先 push P1（`65f60cf`）→ 再开 P2 的 Step 1–5 → 稳定后按需 Phase 2。
