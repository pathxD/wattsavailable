# WattsAvailable

A public-facing website that helps Pacific Northwest utility customers (residential,
commercial, agricultural, industrial) discover the BPA/UES energy-efficiency
incentives their utility may offer, estimate the incentive for their specific
project, and generate a ready-to-send inquiry — citing the exact UES reference
numbers utility program staff use — to kick off the paperwork **before** the
project starts.

**Live site:** https://run206.github.io/wattsavailable/
Preview artifact: https://claude.ai/code/artifact/61cbfc65-c645-4f3f-8d35-d37136a8a7c9

## How it works

- `index.html` — the entire site (UI, styling, matching logic). No framework,
  no build step, no backend. Loads the measure catalog from `data/measures.js`.
- `data/measures.js` — 1,171 active UES measures extracted from BPA's official
  UES Measures List (April 2026, effective 2026-04-01). Expired measures and
  measures without a published payment are filtered out.
- `tools/update_data.py` — regenerates `data/measures.js` from bpa.gov.
  The Implementation Manual and UES list update every April and October.

The user flow: pick sector → building type → heating zone → project type →
see matching measures with BPA reference payments ($/unit) → enter quantities →
build an estimate → generate a text summary (copy / email / print) addressed
to their utility's energy-efficiency team.

Everything runs client-side; no customer data is collected or transmitted.

## Run locally

```bash
python3 -m http.server 8742
# then open http://localhost:8742
```

(Opening index.html directly via file:// also works in most browsers since the
data is a plain script file, not a fetch.)

## Data refresh (automatic)

A GitHub Action (`.github/workflows/update-data.yml`) checks bpa.gov every
Monday and commits refreshed data whenever the published UES Measures List
changes (April and October updates, plus mid-cycle corrections). GitHub Pages
redeploys on push, so the live site updates itself. You can also trigger it
manually from the repo's Actions tab ("Run workflow"), or run it locally:

```bash
pip3 install openpyxl   # once
python3 tools/update_data.py --version "October 2026" --effective 2026-10-01
```

Note: GitHub disables scheduled workflows after ~60 days with no repo
activity — a push or a manual workflow run re-enables them. After each
April/October refresh, spot-check a few measures against the official list.

## Deploy

The site is static — any static host works (Cloudflare Pages, Netlify, GitHub
Pages, S3). Upload `index.html` and `data/measures.js` preserving the relative
path. Suggested domain: **wattsavailable.com** (unregistered as of 2026-08-29;
nwenergymatch.com, nwrebatefinder.com, measurematchnw.com also available).

## Important framing (baked into the site copy)

- Figures are **BPA reference payments to the utility**, not customer quotes.
- Utilities are not required to adopt UES measures; they set final amounts.
- Utility paperwork must be approved **before** work begins.
- BPA reimburses utilities, never end customers; contractors often apply on
  customers' behalf.
- Deemed vs. custom: the utility decides which path applies.
- The site is independent — not affiliated with BPA or any utility.

## Data sources

- Implementation Manual: https://www.bpa.gov/energy-and-services/conservation/implementation-manual
- IM April 2026 (PDF): https://www.bpa.gov/-/media/Aep/energy-efficiency/document-library/IM-April-2026-Final.pdf
- UES Measures List (xlsx): https://www.bpa.gov/-/media/Aep/energy-efficiency/document-library/beets-ues-measure-list.xlsx
- October 2026 update overview: https://www.bpa.gov/-/media/Aep/energy-efficiency/document-library/IM-Oct-26-Update-Announcement.pdf
