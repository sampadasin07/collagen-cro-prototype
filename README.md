# Improved product page: HTML prototype

Responsive HTML prototype of an improved product page for Wellbeing Nutrition’s Pure Korean Marine Collagen Peptides (CRO case study). It implements every section of the spec *HTML Prototype: What to Fix and Build* (`final.pdf`). No backend, payments or analytics.

## Run it
- **Quickest:** open `index.html` in a browser.
- **Local server (recommended):** run `python3 -m http.server 8000` in this folder, then open http://localhost:8000.
- **Host it:** upload this folder to GitHub Pages, Netlify or Vercel. All paths are relative, so it works from any static host.
- **Deck link:** paste your public deck link into `DECK_URL` in `js/data.js`. `about.html` picks it up automatically.

## Files
| File | Purpose |
|---|---|
| `index.html` | Improved product page |
| `checkout.html` | Mock checkout (no payment) |
| `confirmation.html` | Order confirmation (restates pack, method, total) |
| `about.html` | What changed and why, [V] placeholders, what wasn't built, "no results claimed" |
| `js/data.js` | **Single source of truth** for packs, prices, rating, reviews and the shared order logic |
| `js/app.js` | Product page: pack state, price block, sticky bar, reviews filter, "Show what changed" |
| `js/checkout.js` | Checkout: totals, inline validation, hand-off to confirmation |
| `css/styles.css` | Mobile-first styles; laptop layout from 1024 px |
| `img/tub.svg` | Original product illustration (product photos not reused) |
| `tests/test_prototype.py` | Automated Playwright test suite (114 checks) |

## How the pack is carried through the journey
The selected pack is stored in the URL (`index.html?tubs=3` → `checkout.html?tubs=3` → `confirmation.html?tubs=3&pay=online`). Back and Refresh therefore keep the selection. An invalid `?tubs=` value falls back to 1 tub, and checkout shows a note when that happens. Personal details are validated in the browser only; they are never stored or put in a URL.

## Spec coverage (final.pdf)
| § | Requirement | Status |
|---|---|---|
| 1 | Stock count, "allergen-free", MDPI logos, exit pop-up, other timelines, absorption multipliers, "Clinically Proven", "Backed by 20+", second nutrition panel removed; Buy It Now goes straight to checkout | Implemented and tested |
| 2 | Evidence module below benefit icons: usage line, quick facts (2 columns on phone), one nutrition panel with [V] values, ingredient studies with correct publishers, "Tested on this product" with what reports show and don't | Implemented and tested. Lab-report links are a [V] placeholder because the URLs weren't available |
| 3 | Four duration-labelled packs from `data.js`, 1 tub default, "Recommended" on 4 tubs, ₹58/day line, prices and "Save 20%" labels kept, one shared state across radios, sticky bar, price and checkout; optional course note shown with [V] | Implemented and tested |
| 4 | ₹1,439 / MRP ₹1,799; "₹1,367 when you pay online" for 1 tub, [V] for 2–4 tubs; one collapsible "Offers that apply" with 10% OFF, member price, banner offer and [V] stacking rules; free shipping line | Implemented and tested |
| 5 | Non-veg symbol + "Made from fish", allergy line, doctor note, best-before [V], replacement policy + link, vegan link; open on laptop, collapsible on phone; no species named | Implemented and tested |
| 6 | 4.74 / 571 / 424-146-1-0-0; real review near the buy box; [V] dates; "Critical" filter (not default) with "No critical reviews yet"; no marketplace or invented reviews | Implemented and tested |
| 7 | Checkout and confirmation pages; COD ₹1,439 / online ₹1,367 (1 tub); two separate unticked consent boxes, no warning; notice text; inline required and 10-digit validation; no pop-up, timer or scarcity; pack passed by URL | Implemented and tested |
| 8 | Keyboard-accessible "Show what changed" toggle; 7 numbered markers (6 on the product page, 1 at checkout), each with the change and the friction; `about.html` | Implemented and tested. Deck link is [V] until `DECK_URL` is set |
| 9 | Phone: one column in the specified order with a sticky bar; laptop: two columns; no horizontal scroll; targets ≥ 44 px; body text 16 px | Implemented and tested at 360, 390, 414, 1024 and 1440 px |
| 10 | Nothing from the "Do not build" list present | Tested (text scan of shop pages and code review) |

## Test results
Run `tests/test_prototype.py` against a local server on port 8765 (it needs Playwright). Last run: **114 / 114 passed**. The suite checks:
- **Content:** prohibited text absent on all shop pages.
- **Pack selector:** every pack's price, MRP, sticky bar and URL; keyboard arrow selection.
- **Panels and evidence:** offers and suitability behaviour; evidence position and content.
- **Reviews:** rating figures and the filter.
- **"Show what changed":** toggle by keyboard, markers.
- **Journey:** Buy It Now → checkout for all packs, COD vs online totals, consent boxes, validation (empty and 9-digit), confirmation, invalid parameter, Back and Refresh.
- **Layout:** no horizontal scroll, target sizes, font size, sticky bar, mobile order and laptop columns at five widths.
- **Integrity:** internal links and anchors, images, console errors.

**Not tested here:**
- **Real devices:** I tested in headless Chromium with phone-sized viewports, not on real phones or in Safari or Firefox. Please check once on your own phone.
- **Screen readers:** not tested, beyond semantic markup and keyboard checks.

## Unresolved items ([V] placeholders)
- **Product data:** nutrition values (7.9 g vs 7.45 g protein); online price for 2–4 tubs; offer-stacking rules and "Get 10% OFF" terms; batch best-before date; whether 100 days "covers the 3–4 month course" (100 days covers only the 3-month minimum).
- **Reviews:** review dates, and the text of the single 3★ rating.
- **Evidence:** lab-report links, full study citations, and the publisher of *Orthopedic Reviews*.
- **Deck:** the deck URL.

## Notes on content
- **Prices:** as observed on the live page on 21 Oct 2026, matching the strategy deck. The live price changed after that date.
- **Reviews:** copied from the live page as captured. Several real "Verified" 5★ entries contain only the product name, and they are shown as-is.
- **FAQ:** a short subset of the live FAQ. Answers that gave a different results timeline were aligned to the pack-label usage line.
- **No live-site source code:** the live site's source code wasn't available, so this prototype is a standalone rebuild using the live page's content.
