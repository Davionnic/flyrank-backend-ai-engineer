# messy notes — polite-scraper (BE-05)

problem: need a scraper assignment that proves politeness (delay, UA, cache) without looking like a reckless crawl of a real site.
educational scraper against books.toscrape.com sandbox (explicit practice site).
projects/polite-scraper/

scope: first 3 catalogue pages ~60 unique books.
outputs: output/books.json + output/run-report.json + cache/ (gitignored)

politeness:
- min 500ms between live requests
- User-Agent FlyRankBE05Bot/1.0 (Davionnic; educational)
- cache HTML so reruns dont hammer the sandbox
robots.txt was 404 on target; meta robots NOARCHIVE,NOCACHE — not a scrape ban

schema via pydantic: title, product_url, price_gbp, availability_text, rating_text, description, source_page, fetched_at

honest framing: practice sandbox, not a client scrape. no "we scraped the web at scale" nonsense.
proof of run: committed books.json / run-report.json in repo.
