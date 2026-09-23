# PF-04 submission — personal portfolio

## Live URL

https://davionnic.github.io/flyrank-backend-ai-engineer/

## What shipped

- Multipage static site: Home (`index.html`), Work (`work.html`), About/Contact (`about.html`)
- Proof claim + email CTA: `gallodave.cs@gmail.com` (junior backend / AI-adjacent)
- FlyRank graduate badge → https://internship.flyrank.ai/verify
- CV: `cv.md`
- Dynamic feature: validated mailto contact form + clipboard fallback (`FEATURE.md`)
- Mobile-friendly CSS, SVG favicon, OG/meta tags
- Analytics: **pending** (no GA ID; documented in README)
- LinkedIn: **TBD** — search link used; no confirmed public profile URL at ship

## DNS walkthrough (short)

GitHub Pages free host `davionnic.github.io` serves this repo at path `/flyrank-backend-ai-engineer/`. No custom domain, no CNAME you manage. HTTPS from GitHub. Full notes: `DNS-WALKTHROUGH.md`.

## Deploy

- Workflow: `.github/workflows/pages.yml`
- Source dir: `projects/personal-site/`

## Portal paste block

```
Live: https://davionnic.github.io/flyrank-backend-ai-engineer/
Email CTA: gallodave.cs@gmail.com
Verify: https://internship.flyrank.ai/verify
Feature: mailto contact form (FEATURE.md)
DNS: github.io project Pages, no custom domain (DNS-WALKTHROUGH.md)
```
