# FEATURE: Contact form (mailto + clipboard fallback)

## What it does

One real dynamic feature on the static site: a contact form that works without a paid backend, Formspree ID, or Netlify functions.

1. User fills Name, Email, optional Company, Message on `about.html`.
2. Client-side JS (`form.js`) validates:
   - name non-empty
   - email looks like an address
   - message ≥ 10 characters
3. On submit, JS builds a plain-text body and opens:

   `mailto:gallodave.cs@gmail.com?subject=Junior%20backend%20/%20AI-adjacent%20role&body=...`

4. Form hides; a success panel shows.
5. If the mail client does not open (mobile/desktop quirks), **Copy message body** puts the same text on the clipboard so the user can paste into any mail app.

## Data flow (plain)

```
Browser form
  → validate (client only)
  → encode fields into mailto URL
  → hand off to OS / browser mail handler
  → user sends from their own inbox
```

No server stores the message. No webhook. No analytics on the submit event.

## Why not Formspree / Issues / webhook.site

- Formspree needs a real form ID — inventing one would break the form.
- GitHub Issues creation needs auth tokens in the browser — wrong for a public portfolio.
- webhook.site URLs expire — not a durable contact path.

## How to test in a browser

1. Open `/about.html#contact`.
2. Submit empty → see validation error (no mail opens).
3. Fill valid fields → mail draft opens (or success + copy works).
4. Confirm subject is `Junior backend / AI-adjacent role` and To is `gallodave.cs@gmail.com`.

## Files

- `about.html` — form markup + success UI
- `form.js` — validate, mailto, clipboard fallback
