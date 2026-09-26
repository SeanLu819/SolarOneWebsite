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

`summary` = 131 chars ✅ (`NewsArticle.summary` usually reused as card text and `og:description`).

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

Photos have been downloaded from the original 中国民航网 article and copied to
`static/images/news/low-cct-high-cri-high-mast-led-retrofit/`. Source files with the
original IDs are kept in the `_source/` sub-folder for provenance.

| file | dimensions | what it shows | suggested use | EN alt |
|---|---|---|---|---|
| `tianjin-binhai-high-mast-retrofit-hero.jpg` | 581×380 (3:2, ~17 KB) | Apron at dusk: airplane on left, high-mast lights on right | ⚠️ **Not recommended as hero** on the current card: it is 3:2 while `news-card-img` enforces `aspect-ratio: 16 / 9`, so it will be heavily cropped; also low resolution for large cards. | Airplane on the apron at dusk with high-mast floodlights in the background, Tianjin Binhai Airport |
| `tianjin-binhai-high-mast-retrofit-ground-work.jpg` | 600×337 (16:9, ~200 KB) | Technicians on the ground assembling LED floodlight modules | ✅ **Recommended hero**. Already close to 16:9, fits the card aspect ratio, and visually tells the main story: the work has moved to ground level. | Technicians assembling LED high-mast floodlight modules at ground level, Tianjin Binhai Airport |
| `tianjin-binhai-high-mast-retrofit-head-work.jpg` | 600×337 (16:9, ~147 KB) | Technician on a ladder servicing the luminaire head | ⚠️ **Cannot be used on the current list page without a code change** — the news list only shows `NewsArticle.image`. Save this for a future news detail page or a project case-study page. | Technician servicing a high-mast luminaire head on a ladder, Tianjin Binhai Airport |

Source URLs (for your records):
- hero / apron: `http://fuwu.caacnews.com.cn/1/5/202608/W020260827591086452823.jpg`
- ground work: `http://fuwu.caacnews.com.cn/1/5/202608/W020260827591086468159.jpg`
- head work: `http://fuwu.caacnews.com.cn/1/5/202608/W020260827591086472965.jpg`

⚠️ All three carry the **中国民航网 watermark** in the corner. If that is not acceptable
for a manufacturer site, you will need to request un-watermarked originals from the
source or use your own photos.

⚠️ Existing code limitation: `templates/news.html:39` renders `alt="{{ article.title }}"`.
Only the hero image gets an alt on the card. The inline images in `content` carry no
alt at all (and cannot, because `content|linebreaks` is plain text).

### If you decide to use one of the 16:9 photos as hero
Set `NewsArticle.image` to:
`tianjin-binhai-high-mast-retrofit-ground-work.jpg`
(or whichever file you pick).

### Optional: convert to .webp
The site generally serves `.webp` elsewhere. If you re-encode these to `.webp` for
better compression, rename them consistently and update this plan. But do **not**
change the filename after uploading — the image pipeline fixes the name on upload.

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
5. If you want to use the third photo (`head-work.jpg`) in the body, you must first add
   a detail page or an inline-image tag that survives rendering — otherwise it cannot
   be displayed.

## Open question for you

1. Which photo do you want as the hero? I recommend `tianjin-binhai-high-mast-retrofit-ground-work.jpg`.
2. Is the 中国民航网 watermark acceptable, or should we swap these out for your own
   product/site photography before publication?
