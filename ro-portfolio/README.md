# krovix — Cybersecurity Portfolio (Rohan Khatri)

A full-stack, cyber-themed portfolio built with **Next.js 14**. Dark "recon report"
aesthetic with a red accent, an animated port-scan hero that doubles as navigation,
floating real certification badges, per-platform lab dashboards (TryHackMe, Hack The
Box, HackerRank, LeetCode), a blog section that previews your latest post and links
out to your blog, and a dedicated contact section.

Everything on the site is driven by editable JSON — no database wrangling required.

## Run it

```bash
npm install
npm run dev      # http://localhost:3000
```

Build for production:

```bash
npm run build
npm start
```

> Note: on very low-powered/sandboxed machines the first `next build` can be slow.
> On a normal laptop it compiles in a few seconds.

## Editing your content (this is the important part)

All content lives in **`/data/*.json`**. Edit a file, save, refresh — done.
No code changes needed.

| File | What it controls |
|------|------------------|
| `data/profile.json` | Name, alias (krovix), tagline, about, email, phone, location, social links, blog URL |
| `data/projects.json` | Every project card — title, severity, status, "why", "solves", tags |
| `data/certifications.json` | Cert name, issuer, status, and `logo` (badge image URL or local file) |
| `data/experience.json` | Work history timeline |
| `data/education.json` | Education timeline |
| `data/labs.json` | TryHackMe / HTB / HackerRank / LeetCode cards — rank, progress %, stats, profile URL, username |
| `data/hobbies.json` | The "off the clock" chips |
| `data/blogs.json` | Your blog URL + the latest post preview (see below) |

### Certification badges (the real logos)

`certifications.json` already points at the **official Credly badge images** for
Security+, ISC2 CC, Splunk Core, BTL1, AWS Cloud Practitioner, AWS AI Practitioner,
and Google Cybersecurity — the same images shown on your Credly profile.

- **SC-200 / SC-900** use Microsoft's official credential badge art.
- **TryHackMe SOC L1** — TryHackMe doesn't publish an embeddable badge, so it uses a
  styled local badge at `public/certs/thm-soc1.svg`. To use your real certificate,
  drop a PNG into `public/certs/` and point the `logo` field at it, e.g.
  `"logo": "/certs/my-thm-cert.png"`.

To swap ANY badge for your personal earned version: open your badge on Credly →
right-click the image → copy image address → paste it into the `logo` field.

### Labs (THM / HTB / HackerRank / LeetCode)

Open `data/labs.json` and replace `YOUR_*_USERNAME` and the profile URLs with yours,
then set each card's `rank`, `progressPct`, and `stats` to your real numbers. Clicking
a card opens your profile on that platform.

### Blog

`data/blogs.json`:

```json
{
  "blogUrl": "https://your-blog.com",
  "latest": {
    "title": "My first CTF writeup",
    "date": "2026-08-01",
    "excerpt": "How I rooted the box...",
    "url": "https://your-blog.com/first-writeup"
  }
}
```

- Set `blogUrl` to your blog's homepage (the "visit the full blog" button).
- Fill in `latest` and the newest post shows on the portfolio, linking straight to it.
- Leave `latest.title` empty and the section shows a tasteful "coming soon" state.

## API (full-stack layer)

Each section is also served over a REST API, so you can wire up a CMS or edit remotely later:

- `GET /api/projects` — returns the JSON
- `PUT /api/projects` — overwrites it (send the full JSON body)

Same pattern for `profile`, `certifications`, `education`, `experience`, `hobbies`, `labs`, `blogs`.

## Deploy free

Push to GitHub, import into **Vercel**, deploy. Zero config.

## Structure

```
app/
  page.js              # the whole homepage
  layout.js
  globals.css          # the red cyber theme
  api/[section]/route.js
components/             # Nav, Scanner (animated hero), Reveal (scroll-in)
data/                  # <-- edit these
public/certs/          # local badge fallbacks
PREVIEW.html           # static preview of the design (open in any browser)
```
