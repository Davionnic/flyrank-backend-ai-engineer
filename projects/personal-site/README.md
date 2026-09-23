# Personal site (PF-04)

Static portfolio for **Dave Andrei Almia Gallo**.

**Live:** https://davionnic.github.io/flyrank-backend-ai-engineer/

## Pages

| File | Role |
|------|------|
| `index.html` | Home — proof claim + CTA |
| `work.html` | Real project links |
| `about.html` | About + contact form |
| `cv.md` | Short CV |
| `FEATURE.md` | Mailto form data flow |
| `DNS-WALKTHROUGH.md` | github.io / HTTPS / no custom domain |
| `SUBMISSION.md` | Portal paste |

## Contact

- Email / booking: [gallodave.cs@gmail.com](mailto:gallodave.cs@gmail.com?subject=Junior%20backend%20/%20AI-adjacent%20role)
- GitHub: https://github.com/Davionnic
- LinkedIn: **TBD** — no confirmed public profile URL found at ship time. Site uses a [LinkedIn search link](https://www.linkedin.com/search/results/all/?keywords=Dave%20Andrei%20Almia%20Gallo). Update when a real profile URL exists.

## Analytics

**Analytics pending.** No Plausible/GA measurement ID on hand. Do **not** add Google Analytics without an ID.

When ready:

1. Pick a privacy-friendly tool (e.g. Plausible) or GA4.
2. Put the script/snippet in all HTML heads.
3. Remove the “Analytics: pending” HTML comments and this section’s “pending” line.

Until then: HTML comments mark the slot; no third-party trackers load.

## Local preview

```bash
cd projects/personal-site
python3 -m http.server 8080
# open http://127.0.0.1:8080/
```

## Deploy

GitHub Actions workflow at repo root: `.github/workflows/pages.yml` publishes this folder to Pages.
