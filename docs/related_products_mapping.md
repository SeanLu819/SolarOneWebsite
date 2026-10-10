# Related Products 后台选择作业清单（22 个项目）

> v1.10.25 起，**自动匹配已删除**。项目页底部的 Related Products 完全由后台手工选择：
> 选了才显示，没选整块不显示（无兜底、无自动生成）。

## 结论先行

1. 后台路径：`/admin/pages/project/<id>/change/` → **Related Products**（左右两栏选择器，可多选）。
   字段定义在 `pages/models.py` 的 `Project.related_products`（M2M → Product）。
2. 保存即生效：admin 保存会自动 `sync_seed_from_db()` 写回 `seed_data.json`
   （生产真源，字段 `related_product_slugs`）。**改完必须 commit + push**，Vercel 才会重建。
3. 本地看效果要**重启 runserver**（进程内缓存；`DEBUG=False` 模板也被 cached loader 缓存）。
4. 当前进度：**1 / 22** 已选（`football-field-led-retrofit` → `fl9m`）。
   其余 21 个项目页上线后该区块是**不显示**的。

## 作业表

「旧规则建议」一列是**改版前**自动规则算出的结果，仅供参考；⚠️ 标记的项目当时结果还会随进程变化
（旧实现用 `set` 迭代），说明规则本身拟合得并不好 —— **以你实际装了什么灯为准**。

| # | 项目 slug | sport_type / venue_type | 旧规则建议（仅供参考） | 后台已选 |
|---|-----------|-------------------------|------------------------|----------|
| 1 | football-field-led-retrofit | FOOTBALL_FIELD / OUTDOOR | vsp-xxxxw-9m-yp, vsp-xxxxw-12m-yp | ✅ fl9m |
| 2 | yuanshen-sports-centre-stadium | SOCCER_FIELD / OUTDOOR | vsp-xxxxw-9m-yp, vsp-xxxxw-12m-yp | |
| 3 | baseball-field-led-retrofit | BASEBALL_FIELD / OUTDOOR | vsp-xxxxw-9m-yp, vsp-xxxxw-12m-yp | |
| 4 | morgan-state-university-tennis-courts | TENNIS_COURTS / OUTDOOR | rt590fl-s, rt390fl, rt220ub | |
| 5 | nanshan-ski-village | SKI_AREA / OUTDOOR | ⚠️ vsp 系列 + rt590fl-s | |
| 6 | multi-sport-arena-hd-broadcast | MULTI_SPORT / INDOOR | ⚠️ vsp 系列 + rt400hb | |
| 7 | narbonne-arena | MULTI_SPORT / INDOOR | ⚠️ vsp 系列 + rt400hb | |
| 8 | beijing-capital-international-airport | AIRPORT / INFRASTRUCTURE | ⚠️ m-series, rt410-series, rgb-rgbw / rt590fl-s 系 | |
| 9 | beijing-international-tennis-center | TENNIS / INDOOR | ⚠️ rt590fl-s 系 / rt400hb 系 | |
| 10 | national-snow-and-ice-research-center | ICE_ARENA / INDOOR | ⚠️ vsp 系列 + rt400hb | |
| 11 | chunan-velodrome | VELODROME / INDOOR | ⚠️ vsp 系列 + rt400hb | |
| 12 | olympic-sports-center-gymnasium-beijing | BASKETBALL / INDOOR | ⚠️ rt590fl-s 系 / rt400hb 系 | |
| 13 | beijing-liu-li-bridge | CITY_EXPRESSWAY / ROADWAY | rt600sl-t, rt820sl-t, rt590fl-s | |
| 14 | fencing-venue-of-the-7th-cism-military-world-games | FENCING / INDOOR | ⚠️ rt590fl-s 系 / rt400hb 系 | |
| 15 | red-1-karting-beijing | KARTING / OUTDOOR | ⚠️ vsp 系列 + rt590fl-s | |
| 16 | yingdong-natatorium | AQUATICS_CENTRE / INDOOR | ⚠️ vsp 系列 + rt400hb | |
| 17 | perryville-high-school | FOOTBALL_FIELD / OUTDOOR | vsp-xxxxw-9m-yp, vsp-xxxxw-12m-yp | |
| 18 | mcintosh-county-academy | FOOTBALL_FIELD / OUTDOOR | vsp-xxxxw-9m-yp, vsp-xxxxw-12m-yp | |
| 19 | garrison-forest-school | SOCCER_FIELD / OUTDOOR | vsp-xxxxw-9m-yp, vsp-xxxxw-12m-yp | |
| 20 | north-creek-community-center | TENNIS_COURTS / OUTDOOR | rt590fl-s, rt390fl, rt220ub | |
| 21 | pickle-n-par-club | TENNIS / INDOOR | ⚠️ rt590fl-s 系 / rt400hb 系 | |
| 22 | national-olympic-sports-center-beijing-tennis-cour | TENNIS_COURTS / OUTDOOR | rt590fl-s, rt390fl, rt220ub | |

## 产品目录（选择时用得上）

| 分类 | slug |
|------|------|
| SPORTS_LIGHTING | `vsp-xxxxw-9m-yp`、`vsp-xxxxw-12m-yp` |
| FLOODLIGHT | `rt590fl-s`、`rt390fl`、`rt220ub`、`rt420fs-s` |
| HIGHBAY_LOWBAY | `rt400hb`、`rt500hb` |
| AREA_SITE | `m-series`、`rt410-series`、`rgb-rgbw`、`fl1m`、`fl4m`、`fl6m`、`fl9m`、`fl12m`、`fl16m`、`fl9m-rgbw`、`rt410-rgbw` |
| ROADWAY | `rt600sl-t`、`rt820sl-t` |
| ACCESSORY | `mseries-gs`、`glare-shield-for-rt410`、`accessory` |

## 注意事项

- 卡片图是 16:9 **contain**（不裁剪）；选好后在 `/projects/<slug>/` 页面底部核对。
- 反向关系（产品页的 Application Cases）**仍是自动的**，不受此表影响。
- 一次选完 22 个项目后，建议 `git diff seed_data.json` 抽查 `related_product_slugs` 再提交。
