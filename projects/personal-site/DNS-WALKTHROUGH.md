# DNS walkthrough — GitHub Pages (free subdomain, budget zero)

## Target URL

**https://davionnic.github.io/flyrank-backend-ai-engineer/**

That is a **project Pages site** for repo `Davionnic/flyrank-backend-ai-engineer`.
No custom domain. No registrar. No Cloudflare. Cost: $0.

## How `github.io` resolves (high level)

1. Browser requests `davionnic.github.io`.
2. Public DNS for `github.io` points at GitHub’s Pages edge (GitHub-managed A/AAAA/CNAME records — you do not edit these for `*.github.io`).
3. TLS certificate is provisioned by GitHub for `*.github.io` (and user/org Pages hosts). HTTPS is on by default for github.io hosts.
4. The path `/flyrank-backend-ai-engineer/` maps to this repository’s published Pages artifact (not a separate DNS record). Path routing is application-level on GitHub’s side.

You are **not** creating a CNAME at a DNS host yet. A future custom domain would look like:

```
yourdomain.com  CNAME  davionnic.github.io
```

plus GitHub Pages “Custom domain” + HTTPS enforcement. Skipped here (budget zero).

## What we deploy

- Source folder in repo: `projects/personal-site/`
- GitHub Actions workflow: `.github/workflows/pages.yml`
- Build type: **GitHub Actions** (not “Deploy from branch” copying `/docs`)
- Artifact = contents of `projects/personal-site` uploaded and published by `actions/deploy-pages`

## Enable / check Pages

```bash
# Create Pages config (workflow builder)
gh api repos/Davionnic/flyrank-backend-ai-engineer/pages -X POST \
  -f build_type=workflow -f source[branch]=main -f source[path]=/

# Or inspect
gh api repos/Davionnic/flyrank-backend-ai-engineer/pages
```

If Pages already exists, PATCH `build_type` to `workflow` instead of POST.

## Verify live

```bash
curl -sI https://davionnic.github.io/flyrank-backend-ai-engineer/ | head
# Expect HTTP/2 200 and text/html
```

First publish can take 1–3 minutes after the workflow finishes. 404 right after merge usually means “wait for the Actions run,” not bad DNS.

## HTTPS

Handled by GitHub for `https://davionnic.github.io/...`. No Let’s Encrypt DIY. No HTTP→HTTPS setup on your side beyond enabling Pages.

## Summary for portal paste

- Free subdomain: `davionnic.github.io`
- Repo path site: `/flyrank-backend-ai-engineer/`
- Deploy: Actions → upload-pages-artifact → deploy-pages from `projects/personal-site`
- Custom domain: none (TBD when budget exists)
- CNAME: not required for github.io project URL
