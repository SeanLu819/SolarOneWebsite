# EN — High-mast LED retrofit case study (news article, draft)

**Status:** 待审（文字 + 图片已处理，站点代码未改动 —— 其他 IDE 正在改站）
**Factual basis:** 中国民航网 / 中国民航报, 2026-08-27, 通讯员冯嵩
《天津滨海机场联合高校攻关高杆灯改造 首台样机实现三大技术突破》
**Important:** this is a *case study + our engineering commentary*, not a claim that
SolarOne worked on the project. Do not add "we delivered it" anywhere — it is not true.

## Field values (for `NewsArticle`)

| field | value |
|---|---|
| `title` | Low-CCT, High-CRI High-Mast LED Retrofit: Inside a 30-Metre Airport Prototype |
| `slug` | `low-cct-high-cri-high-mast-led-retrofit` |
| `published_at` | ⚠️ set on publish date (not yet) |
| `summary` | A 30m airport high-mast retrofit moved its LED drivers to ground level, held 2500K at full efficacy, and hit 100% command delivery. |
| `meta_title` | Low-CCT High-CRI High-Mast LED Retrofit \| SolarOne |
| `meta_description` | How a 30m high-mast LED retrofit moved drivers to the ground, held 2500K without losing efficacy, and reached 100% command delivery. |
| `content` | See **Body below** (plain paragraphs, blank-line separated — the news page runs `\|linebreaks`, so **no markdown, no tables, no images inside `content`**) |
| `image` | see **Image plan** |

`summary` = 186 chars → **over-trim for the card/meta**; final ≤160 version below.

---

## Body (paste into `content`)

> Formatting constraints proven against `templates/news.html:46` (`{{ content|linebreaks }}`):
> separate paragraphs with a **blank line**. A single newline inside a paragraph becomes
> `<br>`, so the bullet list below will render as one paragraph with hard breaks —
> acceptable, but only just. See the hand-off note at the bottom.

---

A 30-metre high mast is one of the least forgiving places on earth to service a luminaire. For decades the standard answer was a hoist: lower the head to the ground every time a lamp fails. That made sense when a 1000 W HID lamp was the thing that failed. It stopped making sense the moment LED took over.

In August 2026, Tianjin Binhai Airport switched on a retrofit that attacks the problem from the other direction. Developed with the aviation lighting innovation lab at Tianjin University of Science and Technology's engineering training centre, the first prototype keeps the luminaire head fixed and brings everything that can wear out down to ground level. The result is not a brighter lamp. It is a maintenance model that no longer requires a 30-metre work at all.

**Moving the driver out of the luminaire head.** Traditional high-mast luminaires hide their drivers up in the head, which is exactly why the hoist exists. Hoists come with wire rope, motors, limit switches and a maintenance burden of their own, and once LED extended the lamp life, the hoist became the most unreliable part of the system. The Tianjin prototype relocates the driver and other consume-able components into a ground-level power control cabinet with active cooling.

The obvious part is the cabinet. The hard part is the 30 metres of cable feeding it. Long DC runs bring voltage drop, conductor heating and insulation safety, and all three have to be solved before the luminaire will hold a stable output. The team built a line model and ran drop simulations to size the conductor and pick a compensation point, then specified bespoke clips for the low-voltage, high-current run. Measured end-of-run voltage sits inside the stable band, and light output stays constant. Daily inspection and part replacement now happen at ground level, which removes the highest-cost item in a high-mast maintenance budget: work at height.

**An isolated network beats a public one.** Airport aprons are among the most electronically hostile environments there are, and public 4G routinely drops commands. Rather than patch the existing link, the team stood up a private low-frequency WAN that is physically isolated from both the public network and the business network, so the apron lighting keeps running even if everything around it goes down. Three things are notable. The frequency band was chosen by sweeping with a spectrum analyser for weeks and finding a clear window between the aviation navigation bands — they did not inherit a band, they claimed one. The protocol was written from scratch with two-way acknowledgement and local caching, so a command still lands even if the acknowledgement never travels back. And the architecture is isolated by design, not by preference. Across dozens of remote commands, response time came in at millisecond level and command delivery rose from under 90 percent on public LTE to 100 percent.

**2500K without paying for it in efficacy or CRI.** Aviation apron lighting must sit below 4000K, and the crews used to HID know why: traditional high-pressure sodium runs around 2000K, and that warm white is already familiar to pilots and ground staff. Most LED luminaire options on the shelf can be pushed under 3000K, but doing that usually costs you something else — efficacy and colour rendering drop together as the colour temperature comes down. So this project went upstream instead of shopping. Chip selection, substrate material and phosphor ratio were all specified for the target rather than picked for the catalogue, and it took several formulation rounds and dozens of spectral tunings to land on 2500K while keeping efficacy and CRI intact. Measured on the apron, the light reads reassuringly close to the sodium lamps it replaced.

**What to ask for on your own high-mast project.** If you are specifying an apron, rail yard, port or large plateau retrofit, the Tianjin prototype is a useful template. Ask your supplier to commit to the whole triangle, not one corner of it: colour temperature, luminous efficacy and CRI move together, and any one of them can be quoted to look good in isolation. Ask where the driver lives and how you service it in fifteen years. Ask for a voltage-drop budget on the DC run rather than a cable length. Ask what happens to the lighting control when the public network fails — if the answer depends on the public network, you have not bought a lighting system, you have bought a lighting system with a dependency. And finally, count the hours of work-at-height the design still requires, because that number, not the luminaire price, is what a maintenance manager actually cares about.

**The wider point.** Retrofitting ageing high-mast infrastructure is no longer a choice between replacing it and letting it limp along. As Tianjin's team has shown, one well-chosen prototype can re-engineer the hoist structure, the communications link and the spectrum at the same time, and turn a failing asset into a maintained one without a single new mast. For owners of older lighting infrastructure, that is the interesting decade.

---

## Image plan

⚠️ **Do not use the photos from the original article.** They are © 中国民航报社 /
中国民航网 and were shot by 冯嵩. Reusing them on a commercial site is a copyright
infringement, regardless of attribution.

| slot | asset | filename to use | EN alt | source |
|---|---|---|---|---|
| hero (`NewsArticle.image`) | night apron lit by a high-mast LED luminaire, or a clean product shot of a high-mast/floodlight head | `high-mast-led-retrofit-hero.webp` (1920×1000, <200 KB) | High-mast LED floodlight illuminating an airport apron at night | ⚠️ **you must supply** — your own product/apron photography |
| inline #1 | cutaway diagram: driver relocated from mast head to ground cabinet | `high-mast-driver-relocation-diagram.svg` | Diagram: the LED driver is relocated from the high-mast luminaire head to a ground-level power control cabinet | ✅ I authored this (original, safe to use) — `docs/news/en/high-mast-driver-relocation-diagram.svg` |
| inline #2 (optional) | ground-level maintenance crew / control cabinet | `high-mast-ground-control-cabinet.webp` | Ground-level power control cabinet servicing a high-mast luminaire | ⚠️ optional, only if you have your own |

Notes:
- Naming follows `docs/image-seo-naming-spec.md`: lowercase, hyphen-separated, no caps, no
  underscore, no resolution noise (`1080p`), no redundant product word when the folder
  already says it.
- Admin upload → `media/news/<filename>` → copied to `static/images/news/<slug>/`.
  ⚠️ **The filename is fixed the moment it is uploaded** (see the image-pipeline note in
  project memory). Decide the names above *before* uploading.
- ⚠️ Existing code limitation: `templates/news.html:39` renders `alt="{{ article.title }}"`.
  Only the hero image gets an alt; inline images in `content` carry no alt at all.

## Translation to prepare later

Six languages. Rules already agreed for this project: model numbers and order codes are
never translated; `SolarOne` is never transliterated; do not machine-translate anything
that reads like compliance or safety text.

| lang | title (draft, needs native review) | note |
|---|---|---|
| fr | *Rénovation LED pour mât haut à basse température de couleur et IRC élevé* | verify French aviation lighting vocabulary (éclairage de piste) |
| es | *Reforma LED de mástil alto con baja CCT y alto CRI* | verify Spanish aviation terms (iluminación de plataforma) |
| de | *Hochmast-LED-Nachrüstung mit niedriger Farbtemperatur und hohem CRI* | compound order is long — check meta truncation |
| ru | *Модернизация светодиодных опор освещения* | |
| ar | — | RTL site; ensure Latin model strings are wrapped `dir="ltr"`/`bdi` |

## Hand-off checklist (when the site code is free again — do not do it now)

1. Confirm the slug of the product range you want to link to; the body above deliberately
   contains **no internal links yet** (there is no news detail page in place).
2. Add the article in **all three sources at once**: DB (`NewsArticle` row) +
   `seed_data.json` + regenerate `pages/seed_data.py` via `python -m pages.seed_sync
   --json`. Editing only `seed_data.json` will be silently overwritten by the next admin
   save, because `seed_sync` defaults to DB mode. ⚠️ This is the mistake that already
   reverted the RT410 copy once.
3. Production (`IS_VERCEL`) serves news from seed JSON, so step 2 is what actually
   publishes it.
4. Decide whether `templates/news.html` should gain (a) a news detail page, (b) markdown
   rendering, (c) real `alt` text per image. `content|linebreaks` cannot render the
   bullet list as a real list.

## Open question for you

Do you have your own high-mast / floodlight photography we should use for the hero, or
should the hero be a SolarOne product render? The diagram is ready either way.
