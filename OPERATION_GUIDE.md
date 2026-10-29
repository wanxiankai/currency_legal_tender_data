# Currency Dataset Operation Guide

This guide describes the verified workflow for continuing the local legal-tender
currency image dataset.

Use this together with `README.md`, `currencies.json`, `collection_log.json`,
the files under `docs/`, and the scripts in `tools/`.

## Current Verified State

As of 2026-10-29, the dataset contains:

- 22 countries/currency areas
- 251 total coin/banknote entries
- A passing validation result from `tools/validate_dataset.py`

The top-level index is `currencies.json`. It is a JSON list of country records,
not an object keyed by country name.

## Core Goal

Keep collecting current legal-tender fiat currency images by country, organized as:

```text
<Country>/
  coin/
    <denomination>/
      front_original.<ext>
      back_original.<ext>
      front.jpg
      back.jpg
  banknote/
    <denomination>/
      front_original.<ext>
      back_original.<ext>
      front.jpg
      back.jpg
```

`currencies.json` must contain the local relative paths for every included image.

Include each denomination only when its current front/back images are locally
verified at usable quality. A country may be included with banknotes only,
coins only, or a subset of current denominations. Record unavailable or
inadequate denominations in the country source policy/log; if no denomination
qualifies, skip the country and record the reason in
`docs/CANDIDATE_SOURCES.md`.

## Inclusion Rules

For a country or denomination to be added to `currencies.json`:

- Use current legal-tender / valid circulation issues.
- Prefer official central-bank, reserve-bank, or mint pages.
- `coin` or `banknote` may be an empty list when only the other category has
  verified entries.
- Partial denomination coverage is allowed; include every current denomination
  that passes the front/back, quality, and source checks discovered in the pass.
- Include all official current design variants when the issuer explicitly lists
  multiple current circulating variants for the same denomination.
- Do not include an individual denomination if it lacks a usable front or back
  image.
- Do not include an individual denomination if its only reproducible images are
  too low quality.
  Previous passes rejected images around 50-150 px for coins or 250-350 px wide
  for banknotes unless no better denomination-level source was available and the
  source policy explicitly justified the choice.
- Do not include images with strong specimen overlays, watermarks, or page labels
  that obscure the currency design.
- Keep source attribution and original image URLs in both `currencies.json` and
  `collection_log.json`.

## Proven Collection Patterns

Existing scripts in `tools/` are the best templates. Choose the closest pattern:

- Direct front/back images:
  `add_chile.py`, `add_georgia.py`, `add_kuwait.py`
- Official combined image split into front/back:
  `add_denmark.py`, `add_sweden.py`, `add_switzerland.py`, `add_uruguay.py`
- Official collage/currency sheet cropped by coordinates:
  `add_philippines.py`, `add_united_arab_emirates.py`
- Official page images with many same-denomination variants:
  `add_costa_rica.py`
- Bank Al-Maghrib 2023-series page images:
  `add_morocco.py`
- Central-bank WordPress/media pages with thumbnail variants:
  `add_bahrain.py`

Always inspect one or two resulting images visually when using a new source
layout, especially when splitting or cropping combined images.

## Script Requirements

Each new country should usually get a reproducible script:

```text
tools/add_<country>.py
```

Follow the existing script structure:

- Define `ROOT = Path(__file__).resolve().parents[1]`.
- Define `COUNTRY_DIR = ROOT / "<Country_Folder>"`.
- Use `curl -L --fail --retry 2` with a browser-like user agent for downloads.
- Use Pillow for image processing.
- Save downloaded source files as `front_original.<ext>` and
  `back_original.<ext>`.
- If the official source provides a combined image, also save
  `combined_original.<ext>` and split/crop it into front/back originals.
- Generate final `front.jpg` and `back.jpg` from originals.
- Flatten transparency onto white.
- Center both sides on a white canvas sized to
  `max(front_width, back_width)` x `max(front_height, back_height)`.
- Save final images as JPEG quality 95.
- Record `image_quality` with:
  - `final_width`
  - `final_height`
  - `front_original_width`
  - `front_original_height`
  - `back_original_width`
  - `back_original_height`
  - `normalized_same_size: true`
  - a short `transform` description
- Update or append the country record in `currencies.json`.
- Update `collection_log.json` with status, counts, sources, and notes.

The required item fields checked by the validator are:

```text
name
value
front_view_image
back_view_image
source
years
source_images
original_front_image
original_back_image
original_source_images
image_quality
```

The top-level country fields checked by the validator are:

```text
country
country_en
name
name_en
symbol
code
coin
banknote
```

Most country records also include `source_policy`; keep adding it even though
the current validator does not require it.

## Normalization Helper Pattern

Most scripts use this logic:

1. Open front/back originals with Pillow.
2. Convert to RGBA.
3. Composite onto a white background.
4. Convert to RGB.
5. Create a final white canvas whose width and height are the maximum of the two
   sides.
6. Center each side on that canvas.
7. Save `front.jpg` and `back.jpg`.

This is what makes same-denomination front/back dimensions identical.

When sources include large white borders, labels, or multiple versions, use a
small crop helper and record the crop/split method in `image_quality.transform`
or `image_quality.source_split`.

## Verification Commands

Run the validator after every batch:

```sh
cd /Users/kw/Documents/currency_legal_tender_data
/Users/kw/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 tools/validate_dataset.py
```

Expected success:

```text
Validation passed.
```

Useful status summary:

```sh
python3 - <<'PY'
import json
d=json.load(open('currencies.json'))
print('countries', len(d))
print('items', sum(len(c['coin']) + len(c['banknote']) for c in d))
for c in d:
    print(f"{c['country_en']}|{c['code']}|coins={len(c['coin'])}|banknotes={len(c['banknote'])}")
PY
```

Useful visual QA contact sheet:

```sh
/opt/homebrew/bin/magick montage <Country>/banknote/*/front.jpg <Country>/banknote/*/back.jpg \
  -thumbnail 220x120 -tile 2x -geometry +8+8 /tmp/<country>_banknotes.jpg
```

Then inspect the generated file visually.

Useful image dimension check:

```sh
/opt/homebrew/bin/magick identify <Country>/*/*/*.jpg
```

## Temporary Files And Downloads Hygiene

Formal dataset images must live under country folders only:

```text
<Country>/coin/<denomination>/...
<Country>/banknote/<denomination>/...
```

Do not use `~/Downloads` as an output directory for collection scripts. If a
browser export, PDF render, or manual source inspection creates files outside the
dataset, move only the verified final source images into the correct country
folder and leave `currencies.json` pointing at country-relative paths.

Known non-dataset working leftovers from earlier investigation passes:

- `tmp/taiwan_api/*.json`: cached CBC Currency Museum detail API responses
  created by `tools/add_taiwan.py`.
- `tmp/pdfs/botswana/...`: Botswana PDF and rendered page images from a skipped
  candidate investigation.
- `tmp/pdfs/belize_2025_labeled.pdf` and `tmp/pdfs/belize_labeled_render/...`:
  Belize PDF/render artifacts from a skipped candidate investigation.

These files are not referenced by `currencies.json` and are not part of the
deliverable dataset. Before reporting a final batch, check for accidental output
outside country folders:

```sh
find /Users/kw/Downloads -type f -newermt '2026-07-01' -print
find /Users/kw/Documents/currency_legal_tender_data/tmp -type f -print
```

If the user asks for cleanup, remove only confirmed temporary artifacts after
checking that no path under `tmp/` or `~/Downloads` is referenced from
`currencies.json`, `collection_log.json`, `README.md`, files under `docs/`, or
scripts.

## Documentation Update Rules

After adding a country:

1. Update the status and coverage tables in both `README.md` and
   `README.zh-CN.md`; keep their Chinese content synchronized.
2. Regenerate `docs/COVERAGE.md`:

   ```sh
   python3 tools/render_coverage.py
   ```

3. Add a concise source/method note under `docs/SOURCES.md`.
4. If another country was investigated but skipped, add it under
   `docs/CANDIDATE_SOURCES.md` with:
   - country/currency code
   - investigation date
   - source searched
   - exact reason it was not added

This prevents future agents from repeating already-failed source paths.

## Common Skip Reasons

Skip and document the candidate when:

- Official pages are blocked by Cloudflare, 403, or JS-only shells and no stable
  asset/API path is found.
- Only low-resolution thumbnails are exposed.
- No current banknote or coin denomination has a complete usable front/back pair.
- Source images include strong specimen overlays.
- The page describes current currency but does not expose reproducible image URLs.
- A multi-country currency area needs a modeling decision not yet made.

## Worktree Safety

The dataset folder may be untracked or dirty. Do not revert unrelated files.
Keep changes scoped to:

- `currency_legal_tender_data/<Country>/...`
- `currency_legal_tender_data/tools/add_<country>.py`
- `currency_legal_tender_data/currencies.json`
- `currency_legal_tender_data/collection_log.json`
- `currency_legal_tender_data/README.md`
- `currency_legal_tender_data/README.zh-CN.md`
- `currency_legal_tender_data/docs/`
- this guide

Do not modify app/game code unless the user explicitly asks.

## Recommended Next-Agent Prompt

Use a prompt like this when handing the work to another agent:

```text
You are continuing a local currency-image dataset task in:

/Users/kw/Documents/currency_legal_tender_data

Before doing anything, read:

1. README.md
2. OPERATION_GUIDE.md
3. docs/COVERAGE.md
4. docs/SOURCES.md
5. docs/CANDIDATE_SOURCES.md
6. tools/validate_dataset.py
7. One or two recent add-country scripts, especially the script whose source
   pattern resembles the next country you investigate.

Goal:
Continue adding verified current legal-tender fiat currency data by country.
For each included denomination, collect current front/back images, store them
locally in the existing country -> coin/banknote -> denomination folder
structure, normalize same-denomination front/back images to identical
dimensions, and update currencies.json and collection_log.json. A country may
contain only banknotes, only coins, or partial denomination coverage.

Rules:
- Prefer official central-bank/mint sources.
- Add every verified current denomination with adequate-quality front/back images;
  the other category and unavailable denominations may remain empty/omitted.
- If no current denomination qualifies, do not add that country; instead record
  the failed candidate and reason in docs/CANDIDATE_SOURCES.md.
- Preserve source URLs and image-quality metadata.
- Follow the existing script patterns in tools/.
- Run the validator after every batch:
  /Users/kw/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 tools/validate_dataset.py
- Regenerate the coverage document after index changes:
  python3 tools/render_coverage.py
- Do a quick visual QA contact sheet for any country whose images are split or
  cropped from combined source images.
- Keep changes scoped to currency_legal_tender_data.

Start by validating the current dataset, summarizing the current country/item
counts, then investigate one promising new country. If it passes the inclusion
rules, add a reproducible tools/add_<country>.py script, generate the images,
update JSON/log/README/docs, and verify.
```

## Completion Criteria

Do not mark the overall project complete merely because validation passes after
one batch. The broader goal is ongoing until the desired global coverage has been
collected or the user explicitly narrows the scope.

A single batch is complete only when:

- Every included denomination is verified under the documented scope, or a
  candidate with no qualifying denomination was documented as skipped.
- `currencies.json` paths point to local files.
- Every included final front/back pair has identical dimensions.
- `collection_log.json`, `README.md`, and the relevant `docs/` files are updated.
- `tools/validate_dataset.py` passes.
- Any split/crop-heavy source has been visually spot-checked.
