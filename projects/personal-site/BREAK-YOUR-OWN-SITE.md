# Break Your Own Site

**Dave Andrei Almia Gallo · Plant / polish pass**

**Live target:** https://davionnic.github.io/flyrank-backend-ai-engineer/

**Checked:** 2026-09-23 21:23 CST (Asia/Shanghai) via curl from the box (no CloudAgent).

Raw log: [break-site-evidence/curl-checks.txt](./break-site-evidence/curl-checks.txt)

---

## What I ran

```bash
BASE=https://davionnic.github.io/flyrank-backend-ai-engineer
# Internal HEAD on pages + assets
curl -sS -o /dev/null -w "%{http_code} %{url_effective}\n" -I "$BASE/"
# … index, about, work, cv.md, favicon, css, js, 404, FEATURE, README, DNS, SUBMISSION
# Deliberate miss:
curl -I "$BASE/bogus-missing-page.html"   # expect 404

# External links from HTML (follow redirects)
curl -I -L https://internship.flyrank.ai/verify
curl -I -L https://github.com/Davionnic
curl -I -L https://github.com/Zeref538/ACRA
curl -I -L https://acra-sandy.vercel.app
# …

# Meta / badge / favicon from live HTML
curl -sS "$BASE/" | rg -n "FlyRank|og:|twitter:|favicon|Analytics"

# Lighthouse
command -v lighthouse || echo "lighthouse-cli not installed; skipped"
```

Empty contact form: **cannot fully exercise** without a browser JS runtime (mailto opens the client). Client-side required fields are in `form.js` + `about.html`; classified as known limitation for this shell pass.

---

## Link check results

### Internal (all expected 200 unless noted)

| Code | URL |
|------|-----|
| 200 | `/` `/index.html` `/about.html` `/work.html` `/cv.md` |
| 200 | `/favicon.svg` `/styles.css` `/form.js` `/404.html` |
| 200 | `/FEATURE.md` `/README.md` `/DNS-WALKTHROUGH.md` `/SUBMISSION.md` |
| 404 | `/bogus-missing-page.html` (control — good) |

### External

| Code | URL | Notes |
|------|-----|-------|
| 200 | https://internship.flyrank.ai/verify | FlyRank badge target |
| 200 | https://github.com/Davionnic | |
| 200 | https://github.com/Davionnic/flyrank-backend-ai-engineer | |
| **404** | https://github.com/Zeref538/ACRA | **Private repo** — unauthenticated HEAD is 404 |
| 200 | https://acra-sandy.vercel.app | Public demo — real proof |
| 200 | https://davionnic.github.io/empty-but-live/ | |
| 200 | LinkedIn search URL | Redirects through login wall; search link is intentional TBD |

---

## Meta / social / favicon (from live HTML)

| Check | Result |
|-------|--------|
| `<title>` | Present — “Dave Andrei Almia Gallo — Backend / AI-adjacent” |
| `meta name=description` | Present |
| `og:title` `og:description` `og:type` `og:url` | Present on index |
| `twitter:card` | Present on index (summary) |
| Favicon | `favicon.svg` 200; SVG with DG mark |
| FlyRank badge | Link text “FlyRank graduate — verify” → internship.flyrank.ai/verify |
| `og:image` | **Missing** — social preview uses title/description only |
| Analytics | Comment says pending — no tracker loaded (correct) |

---

## Lighthouse

**Skipped.** `lighthouse` CLI not installed in this environment. Not faked. Install later with `npm i -g lighthouse` and re-run against the live URL if needed.

---

## Classification

### Fix now (done in this commit)

1. **ACRA GitHub 404 looks like a dead link** — updated `work.html` copy: demo first, repo labeled private / expect 404 logged out.
2. **Missing `twitter:card` on about.html / work.html** — added `summary` to match index.

### Known limitations (not urgent / not fakeable here)

| Item | Why it’s left |
|------|----------------|
| Empty form E2E | Needs browser; mailto can’t be asserted by curl |
| ACRA repo private | Intentional; demo is public |
| LinkedIn = search URL | No confirmed profile URL at ship time (README TBD) |
| No `og:image` | Would need a real preview asset; title/desc still set |
| Analytics pending | No measurement ID — do not invent GA |
| Lighthouse skipped | CLI absent |
| `cv.md` served as raw Markdown | Fine for Pages; not HTML-styled |

---

## After-fix note

Pages deploy is via `.github/workflows/pages.yml`. After this commit lands on `main`, wait for the workflow, then re-curl `/work.html` to confirm the ACRA private-label text is live.
