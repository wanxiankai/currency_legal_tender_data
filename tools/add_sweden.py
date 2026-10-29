#!/usr/bin/env python3
"""Add Sweden SEK valid banknotes and coins from Sveriges Riksbank."""

from __future__ import annotations

import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Sweden"
VALID_BANKNOTES_SOURCE = (
    "https://www.riksbank.se/en-gb/payments--cash/notes--coins/notes/valid-banknotes/"
)
VALID_COINS_SOURCE = (
    "https://www.riksbank.se/en-gb/payments--cash/notes--coins/coins/valid-coins/"
)


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        dest.write_bytes(response.read())


def flatten(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    canvas = Image.new("RGBA", rgba.size, "white")
    canvas.alpha_composite(rgba)
    return canvas.convert("RGB")


def normalize(front_original: Path, back_original: Path, front: Path, back: Path) -> dict[str, Any]:
    with Image.open(front_original) as front_image, Image.open(back_original) as back_image:
        front_rgb = flatten(front_image)
        back_rgb = flatten(back_image)
        final_width = max(front_rgb.width, back_rgb.width)
        final_height = max(front_rgb.height, back_rgb.height)

        def center(image: Image.Image) -> Image.Image:
            canvas = Image.new("RGB", (final_width, final_height), "white")
            canvas.paste(
                image,
                ((final_width - image.width) // 2, (final_height - image.height) // 2),
            )
            return canvas

        center(front_rgb).save(front, "JPEG", quality=95, optimize=True)
        center(back_rgb).save(back, "JPEG", quality=95, optimize=True)

        return {
            "final_width": final_width,
            "final_height": final_height,
            "front_original_width": front_image.width,
            "front_original_height": front_image.height,
            "back_original_width": back_image.width,
            "back_original_height": back_image.height,
            "normalized_same_size": True,
            "transform": (
                "original images flattened onto white, centered on white canvas sized "
                "to max(front, back) for the denomination; JPEG quality 95"
            ),
        }


def make_banknote(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "banknote" / item["name"]
    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["front_url"], front_original)
    download(item["back_url"], back_original)
    quality = normalize(front_original, back_original, front, back)

    return item_record(item, front, back, front_original, back_original, quality)


def make_coin(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "coin" / item["name"]
    combined_original = denomination_dir / "combined_original.png"
    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["combined_url"], combined_original)
    with Image.open(combined_original) as combined:
        midpoint = combined.width // 2
        combined.crop((0, 0, midpoint, combined.height)).save(front_original)
        combined.crop((midpoint, 0, combined.width, combined.height)).save(back_original)

    quality = normalize(front_original, back_original, front, back)
    record = item_record(item, front, back, front_original, back_original, quality)
    record["combined_original_image"] = combined_original.relative_to(ROOT).as_posix()
    record["combined_source_image"] = item["combined_url"]
    record["image_quality"]["coin_split"] = (
        "Riksbank official front/back combined coin image split at the horizontal midpoint; "
        "left half treated as front, right half treated as back."
    )
    return record


def item_record(
    item: dict[str, Any],
    front: Path,
    back: Path,
    front_original: Path,
    back_original: Path,
    quality: dict[str, Any],
) -> dict[str, Any]:
    front_url = item.get("front_url", item.get("combined_url"))
    back_url = item.get("back_url", item.get("combined_url"))
    return {
        "name": item["name"],
        "value": item["value"],
        "front_view_image": front.relative_to(ROOT).as_posix(),
        "back_view_image": back.relative_to(ROOT).as_posix(),
        "source": item["source"],
        "years": item["years"],
        "issued": item["issued"],
        "source_images": {"front": front_url, "back": back_url},
        "original_front_image": front_original.relative_to(ROOT).as_posix(),
        "original_back_image": back_original.relative_to(ROOT).as_posix(),
        "original_source_images": {"front": front_url, "back": back_url},
        "image_quality": quality,
    }


BANKNOTES = [
    {
        "name": "20瑞典克朗",
        "value": 20,
        "years": "2015-present",
        "issued": "1 October 2015",
        "source": "https://www.riksbank.se/en-gb/payments--cash/notes--coins/notes/valid-banknotes/20-krona-banknote/",
        "front_url": "https://www.riksbank.se/contentassets/56def20a399b459bb15521a6a937af1c/20-kronorssedel-navigation-specimen-fram.png",
        "back_url": "https://www.riksbank.se/contentassets/56def20a399b459bb15521a6a937af1c/20-kronorssedel-navigation-specimen-bak.png",
    },
    {
        "name": "50瑞典克朗",
        "value": 50,
        "years": "2015-present",
        "issued": "1 October 2015",
        "source": "https://www.riksbank.se/en-gb/payments--cash/notes--coins/notes/valid-banknotes/50-krona-banknote/",
        "front_url": "https://www.riksbank.se/contentassets/c2b34515579241d5a211fcfcd89f1dc9/50-kronorssedel-navigation-specimen-fram.png",
        "back_url": "https://www.riksbank.se/contentassets/c2b34515579241d5a211fcfcd89f1dc9/50-kronorssedel-navigation-specimen-bak.png",
    },
    {
        "name": "100瑞典克朗",
        "value": 100,
        "years": "2016-present",
        "issued": "3 October 2016",
        "source": "https://www.riksbank.se/en-gb/payments--cash/notes--coins/notes/valid-banknotes/100-krona-banknote/",
        "front_url": "https://www.riksbank.se/contentassets/ec0fcae299064c80871e8ccf3aa8e89b/100-kronorssedel-specimen-fram.png",
        "back_url": "https://www.riksbank.se/contentassets/ec0fcae299064c80871e8ccf3aa8e89b/100-kronorssedel-specimen-bak.png",
    },
    {
        "name": "200瑞典克朗",
        "value": 200,
        "years": "2015-present",
        "issued": "1 October 2015",
        "source": "https://www.riksbank.se/en-gb/payments--cash/notes--coins/notes/valid-banknotes/200-krona-banknote/",
        "front_url": "https://www.riksbank.se/contentassets/8bd04134e5c046b38232d355d9bb8a75/200-kronorssedel-specimen-fram.png",
        "back_url": "https://www.riksbank.se/contentassets/8bd04134e5c046b38232d355d9bb8a75/200-kronorssedel-specimen-bak.png",
    },
    {
        "name": "500瑞典克朗",
        "value": 500,
        "years": "2016-present",
        "issued": "3 October 2016",
        "source": "https://www.riksbank.se/en-gb/payments--cash/notes--coins/notes/valid-banknotes/500-krona-banknote/",
        "front_url": "https://www.riksbank.se/contentassets/e6e9874c29a44edc96d38442e173865d/500-kronorssedel-specimen-fram.png",
        "back_url": "https://www.riksbank.se/contentassets/e6e9874c29a44edc96d38442e173865d/500-kronossedel-specimen-bak.png",
    },
    {
        "name": "1000瑞典克朗",
        "value": 1000,
        "years": "2015-present",
        "issued": "1 October 2015",
        "source": "https://www.riksbank.se/en-gb/payments--cash/notes--coins/notes/valid-banknotes/1000-krona-banknote/",
        "front_url": "https://www.riksbank.se/contentassets/352d05bdefae4a7387f5bf27a795b4f2/1000-kronossedel-specimen-fram.png",
        "back_url": "https://www.riksbank.se/contentassets/352d05bdefae4a7387f5bf27a795b4f2/1000-kronosssedel-specimen-bak.png",
    },
]


COINS = [
    {
        "name": "1瑞典克朗",
        "value": 1,
        "years": "2016-present",
        "issued": "October 2016",
        "source": "https://www.riksbank.se/en-gb/payments--cash/notes--coins/coins/valid-coins/1-krona-coin/",
        "combined_url": "https://www.riksbank.se/contentassets/6364277dd6424b99bf6ea475a5808411/1-krona_-fram--och-baksida.png",
    },
    {
        "name": "2瑞典克朗",
        "value": 2,
        "years": "2016-present",
        "issued": "October 2016",
        "source": "https://www.riksbank.se/en-gb/payments--cash/notes--coins/coins/valid-coins/2-krona-coin/",
        "combined_url": "https://www.riksbank.se/contentassets/b05d3de647a14de4845837c2e1987868/2-krona_-fram--och-baksida.png",
    },
    {
        "name": "5瑞典克朗",
        "value": 5,
        "years": "2016-present",
        "issued": "October 2016",
        "source": "https://www.riksbank.se/en-gb/payments--cash/notes--coins/coins/valid-coins/5-krona-coin/",
        "combined_url": "https://www.riksbank.se/contentassets/ee2079218cee4f3784f7848c34c766e6/5-krona_-fram--och-baksida.png",
    },
    {
        "name": "10瑞典克朗",
        "value": 10,
        "years": "2001-present",
        "issued": "2001",
        "source": "https://www.riksbank.se/en-gb/payments--cash/notes--coins/coins/valid-coins/10-krona-coin/",
        "combined_url": "https://www.riksbank.se/contentassets/d946fd385a7e4edc98b424b6856261d4/10-krona_-fram--och-baksida.png",
    },
]


def main() -> int:
    if COUNTRY_DIR.exists():
        shutil.rmtree(COUNTRY_DIR)

    country_record = {
        "country": "瑞典",
        "country_en": "Sweden",
        "name": "瑞典克朗",
        "name_en": "Swedish krona",
        "symbol": "kr",
        "code": "SEK",
        "source_policy": (
            "Sveriges Riksbank valid banknote and valid coin pages were collected on "
            "2026-07-04. The valid pages list the included legal-tender denominations; "
            "individual denomination pages provide banknote front/back specimen images "
            "and official coin front/back combined images."
        ),
        "coin": [make_coin(item) for item in COINS],
        "banknote": [make_banknote(item) for item in BANKNOTES],
    }

    currencies_path = ROOT / "currencies.json"
    currencies = json.loads(currencies_path.read_text(encoding="utf-8"))
    currencies = [record for record in currencies if record.get("code") != "SEK"]
    currencies.append(country_record)
    currencies_path.write_text(
        json.dumps(currencies, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    log["generated_at"] = now
    log.setdefault("runs", []).append(
        {
            "source": "Sveriges Riksbank",
            "country": "Sweden",
            "collected_at": now,
            "coin_count": len(COINS),
            "banknote_count": len(BANKNOTES),
            "valid_banknotes_source": VALID_BANKNOTES_SOURCE,
            "valid_coins_source": VALID_COINS_SOURCE,
            "sources": sorted({item["source"] for item in COINS + BANKNOTES}),
        }
    )
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
