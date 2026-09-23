# Step 1 — Extracted bullets

- TITLE: messy notes — polite-scraper (BE-05)
- problem: need a scraper assignment that proves politeness (delay, UA, cache) without looking like a reckless crawl of a real site.
- scope: first 3 catalogue pages ~60 unique books.
- outputs: output/books.json + output/run-report.json + cache/ (gitignored)
- politeness:
- min 500ms between live requests
- User-Agent FlyRankBE05Bot/1.0 (Davionnic; educational)
- cache HTML so reruns dont hammer the sandbox
- proof of run: committed books.json / run-report.json in repo.
