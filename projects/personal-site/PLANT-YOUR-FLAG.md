# Plant Your Flag — evidence pack

**Dave Andrei Almia Gallo**

Live portfolio for FlyRank “Plant Your Flag.”

---

## Live URL

**https://davionnic.github.io/flyrank-backend-ai-engineer/**

- Host: GitHub Pages (`davionnic.github.io`)
- Path: `/flyrank-backend-ai-engineer/` (project site from this monorepo)
- Free subdomain: **yes** — `*.github.io` (no custom domain purchased)
- Walkthrough: [DNS-WALKTHROUGH.md](./DNS-WALKTHROUGH.md)

---

## HTTPS verified

```bash
curl -sS -o /dev/null -w "http_code=%{http_code} ssl_verify_result=%{ssl_verify_result} scheme=%{scheme}\n" \
  https://davionnic.github.io/flyrank-backend-ai-engineer/
# Observed 2026-09-23 21:23 CST:
# http_code=200 ssl_verify_result=0 scheme=https
```

`ssl_verify_result=0` means TLS verified successfully.

Evidence also in [break-site-evidence/curl-checks.txt](./break-site-evidence/curl-checks.txt).

---

## FlyRank badge present

From live `index.html` (and mirrored in repo `index.html` / `work.html`):

```html
<a class="badge" href="https://internship.flyrank.ai/verify" …>
  FlyRank graduate — verify
</a>
```

Verify:

```bash
curl -sS https://davionnic.github.io/flyrank-backend-ai-engineer/ | rg -n "FlyRank|internship.flyrank.ai/verify"
# Badge link returns HTTP 200
curl -sS -o /dev/null -w "%{http_code}\n" -I https://internship.flyrank.ai/verify
```

---

## Analytics — pending (not faked)

**Status:** pending. No Plausible/GA measurement ID on hand.

- HTML head comment: `<!-- Analytics: pending — … -->`
- Footer text: “Analytics pending (see README)”
- No third-party analytics script loads.

**How to add later**

1. Create a Plausible (preferred) or GA4 property.
2. Put the official snippet in every HTML `<head>` (`index.html`, `about.html`, `work.html`, `404.html`).
3. Remove “Analytics: pending” comments and update [README.md](./README.md) Analytics section.
4. Do **not** commit a placeholder tracking ID.

Screenshot of a live analytics dashboard: **cannot provide** without a real property. Do not paste a fake screenshot.

---

## Titles / favicon / social preview (from HTML source)

Verified against live index + repo sources:

| Item | Value |
|------|--------|
| `<title>` | Dave Andrei Almia Gallo — Backend / AI-adjacent |
| `meta description` | Backend-focused CS undergrad. Ships services that put AI behind real checks… |
| `og:title` | same as title |
| `og:description` | Ships backend services that put AI behind real checks… |
| `og:url` | https://davionnic.github.io/flyrank-backend-ai-engineer/ |
| `og:type` | website |
| `twitter:card` | summary |
| Favicon | `favicon.svg` (SVG “DG”), `link rel=icon` present, HTTP 200 |
| `og:image` | not set yet (known limitation — see BREAK-YOUR-OWN-SITE) |

```bash
curl -sS https://davionnic.github.io/flyrank-backend-ai-engineer/ \
  | rg -n "<title>|description|og:|twitter:|favicon"
curl -sS -o /dev/null -w "%{http_code}\n" \
  https://davionnic.github.io/flyrank-backend-ai-engineer/favicon.svg
```

---

## Related

- Site break pass: [BREAK-YOUR-OWN-SITE.md](./BREAK-YOUR-OWN-SITE.md)
- Portal paste: [SUBMISSION.md](./SUBMISSION.md)
- Feature (mailto form): [FEATURE.md](./FEATURE.md)
