/**
 * Cloudflare Worker speed probe — measure TTFB *from wherever the visitor is*.
 *
 * Why this file exists
 * --------------------
 * A probe run on the dev box only measures the dev box's network path. To know
 * what a customer in London or Chicago actually waits, you need a request that
 * *originates* in those places. This Worker does exactly that: it sits on the
 * Cloudflare edge, is invoked by someone in the target country, and fetches
 * the site from that same edge — so the measured time includes that country's
 * real round-trip cost.
 *
 * Cloudflare resolves `fetch()` when the RESPONSE HEADERS arrive, so the
 * timestamp right after `await fetch(...)` is effectively TTFB. Waiting for
 * the body afterwards gives total download time. Both are reported.
 *
 * Deploy (no wrangler needed)
 * ---------------------------
 * 1. Cloudflare Dashboard -> Workers and Pages -> Create -> Deploy Worker
 * 2. Name it `perf-probe`, paste this file into the editor
 * 3. Save and Deploy
 * 4. Open, from a machine in the country you care about:
 *      https://perf-probe.<your-subdomain>.workers.dev/?url=https://www.solaronelighting.com/
 *    ...or just send that link to a contact in that country.
 *
 * The response reports `cf.colo`, so even if you open the link yourself while
 * travelling you will always see which edge actually ran the probe.
 *
 * Hardening
 * ---------
 * `ALLOWED_HOSTS` keeps this from becoming an open proxy: without it, anyone
 * could point the Worker at their own origin and burn your free request quota.
 */

const ALLOWED_HOSTS = [
  'www.solaronelighting.com',
  'solaronelighting.com',
];

const DEFAULTS = {
  runs: '3',
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const target = url.searchParams.get('url') || 'https://www.solaronelighting.com/';

    if (url.pathname !== '/') {
      return json({ error: 'probe worker: hit the root path', usage: '/?url=<target>' });
    }

    let host;
    try {
      host = new URL(target).hostname;
    } catch (err) {
      return json({ error: 'bad url parameter', detail: String(err) });
    }
    if (!ALLOWED_HOSTS.some((allowed) => host === allowed || host.endsWith('.' + allowed))) {
      return json({ error: 'host not allowed', host });
    }

    const runs = Math.min(Math.max(parseInt(url.searchParams.get('runs') || DEFAULTS.runs, 10) || 3, 1), 10);

    const samples = [];
    let last = null;
    for (let i = 0; i < runs; i += 1) {
      const started = Date.now();
      let status = null;
      let ttfb = null;
      let total = null;
      try {
        // Headers arrive first: the clock after this line is the TTFB.
        const response = await fetch(target, {
          method: 'GET',
          redirect: 'follow',
          headers: { 'user-agent': 'SolarOnePerfProbe/1.0' },
        });
        status = response.status;
        ttfb = Date.now() - started;
        await response.text();
        total = Date.now() - started;
        last = {
          serverTiming: response.headers.get('server-timing'),
          vercelCache: response.headers.get('x-vercel-cache'),
          age: response.headers.get('age'),
          contentEncoding: response.headers.get('content-encoding'),
          contentType: response.headers.get('content-type'),
        };
      } catch (err) {
        status = 'error';
        ttfb = null;
        total = null;
        last = { error: String(err && err.message ? err.message : err) };
      }
      samples.push({ run: i + 1, ttfbMs: ttfb, totalMs: total, status });
    }

    const ttfbValues = samples.map((s) => s.ttfbMs).filter((v) => typeof v === 'number').sort((a, b) => a - b);
    const median = ttfbValues.length
      ? ttfbValues[Math.floor(ttfbValues.length / 2)]
      : null;

    return json({
      probeEdge: request.cf && request.cf.colo ? request.cf.colo : null,
      visitorCountry: request.cf && request.cf.country ? request.cf.country : null,
      visitorCity: request.cf && request.cf.city ? request.cf.city : null,
      continent: request.cf && request.cf.continent ? request.cf.continent : null,
      target,
      runs,
      medianTtfbMs: median,
      bestTtfbMs: ttfbValues.length ? ttfbValues[0] : null,
      worstTtfbMs: ttfbValues.length ? ttfbValues[ttfbValues.length - 1] : null,
      samples,
      lastResponseHeaders: last,
    });
  },
};

function json(body) {
  return new Response(JSON.stringify(body, null, 2), {
    status: 200,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      'access-control-allow-origin': '*',
    },
  });
}
