#!/usr/bin/env python3
"""Add Philippines PHP current banknotes and coins from Bangko Sentral ng Pilipinas."""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Philippines"
BASE_URL = "https://www.bsp.gov.ph"
NGC_BANKNOTES_SOURCE = (
    "https://www.bsp.gov.ph/SitePages/CoinsAndNotes/"
    "NewGenerationCurrencyBanknotes.aspx"
)
POLYMER_BANKNOTES_SOURCE = (
    "https://www.bsp.gov.ph/SitePages/CoinsAndNotes/PolymerBanknote.aspx"
)
NGC_COINS_SOURCE = (
    "https://www.bsp.gov.ph/Pages/CoinsAndNotes/Coins/"
    "NewGenerationCurrencyCoinSeries.aspx"
)


def absolute(path: str) -> str:
    return urllib.parse.urljoin(BASE_URL, path)


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "curl",
            "--http1.1",
            "-L",
            "-A",
            (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
            ),
            "--retry",
            "2",
            "--connect-timeout",
            "20",
            "--max-time",
            "60",
            url,
            "-o",
            str(dest),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


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


def crop_alpha_within(image: Image.Image, rough_box: tuple[int, int, int, int], margin: int = 8) -> Image.Image:
    crop = image.convert("RGBA").crop(rough_box)
    alpha = crop.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError(f"No alpha content found inside crop box {rough_box}")

    left = max(0, bbox[0] - margin)
    top = max(0, bbox[1] - margin)
    right = min(crop.width, bbox[2] + margin)
    bottom = min(crop.height, bbox[3] + margin)
    return crop.crop((left, top, right, bottom))


def crop_white_border(image: Image.Image, threshold: int = 246, margin: int = 8) -> Image.Image:
    rgb = image.convert("RGB")
    pixels = rgb.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = pixels[x, y]
            if min(r, g, b) < threshold:
                xs.append(x)
                ys.append(y)

    if not xs or not ys:
        return rgb

    left = max(0, min(xs) - margin)
    top = max(0, min(ys) - margin)
    right = min(rgb.width, max(xs) + margin + 1)
    bottom = min(rgb.height, max(ys) + margin + 1)
    return rgb.crop((left, top, right, bottom))


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


def make_direct_banknote(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "banknote" / item["name"]
    front_original = denomination_dir / "front_original.jpg"
    back_original = denomination_dir / "back_original.jpg"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["front_url"], front_original)
    download(item["back_url"], back_original)
    quality = normalize(front_original, back_original, front, back)
    return item_record(item, front, back, front_original, back_original, quality)


def make_split_banknote(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "banknote" / item["name"]
    combined_original = denomination_dir / "combined_original.webp"
    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["combined_url"], combined_original)
    with Image.open(combined_original) as combined:
        midpoint = combined.width // 2
        crop_white_border(combined.crop((0, 0, midpoint, combined.height))).save(front_original)
        crop_white_border(combined.crop((midpoint, 0, combined.width, combined.height))).save(back_original)

    quality = normalize(front_original, back_original, front, back)
    record = item_record(item, front, back, front_original, back_original, quality)
    record["combined_original_image"] = combined_original.relative_to(ROOT).as_posix()
    record["combined_source_image"] = item["combined_url"]
    record["image_quality"]["banknote_split"] = (
        "BSP official NGC front/back combined banknote image split at the horizontal "
        "midpoint, then white border trimmed before normalization."
    )
    return record


def make_coin(item: dict[str, Any], combined_original: Path) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "coin" / item["name"]
    denomination_dir.mkdir(parents=True, exist_ok=True)
    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    with Image.open(combined_original) as combined:
        crop_alpha_within(combined, item["front_box"]).save(front_original)
        crop_alpha_within(combined, item["back_box"]).save(back_original)

    quality = normalize(front_original, back_original, front, back)
    record = item_record(item, front, back, front_original, back_original, quality)
    record["combined_original_image"] = combined_original.relative_to(ROOT).as_posix()
    record["combined_source_image"] = item["combined_url"]
    record["image_quality"]["coin_crop"] = (
        "BSP official transparent all-denomination NGC coin image cropped by fixed "
        "rough boxes around the denomination's obverse and reverse; alpha bounds then "
        "tightened with 8 px padding."
    )
    return record


def make_banknote(item: dict[str, Any]) -> dict[str, Any]:
    if "combined_url" in item:
        return make_split_banknote(item)
    return make_direct_banknote(item)


BANKNOTES = [
    {
        "name": "20菲律宾比索",
        "value": 20,
        "years": "2020-present",
        "issued": "2020 enhanced New Generation Currency banknote",
        "source": NGC_BANKNOTES_SOURCE,
        "combined_url": absolute("/Coins%20and%20Notes/New%20Generation%20Currency%20Banknotes/NGC-20-2.webp"),
    },
    {
        "name": "50菲律宾比索",
        "value": 50,
        "years": "2025-present",
        "issued": "First Philippine Polymer Banknote Series, 2025 circulation",
        "source": POLYMER_BANKNOTES_SOURCE,
        "front_url": absolute("/Coins%20and%20Notes/Polymer/50/50obverse.jpg"),
        "back_url": absolute("/Coins%20and%20Notes/Polymer/50/50reverse.jpg"),
    },
    {
        "name": "100菲律宾比索",
        "value": 100,
        "years": "2025-present",
        "issued": "First Philippine Polymer Banknote Series, 2025 circulation",
        "source": POLYMER_BANKNOTES_SOURCE,
        "front_url": absolute("/Coins%20and%20Notes/Polymer/100/100obverse.jpg"),
        "back_url": absolute("/Coins%20and%20Notes/Polymer/100/100reverse.jpg"),
    },
    {
        "name": "200菲律宾比索",
        "value": 200,
        "years": "2020-present",
        "issued": "2020 enhanced New Generation Currency banknote",
        "source": NGC_BANKNOTES_SOURCE,
        "combined_url": absolute("/Coins%20and%20Notes/New%20Generation%20Currency%20Banknotes/NGC-200-2.webp"),
    },
    {
        "name": "500菲律宾比索",
        "value": 500,
        "years": "2025-present",
        "issued": "First Philippine Polymer Banknote Series, 2025 circulation",
        "source": POLYMER_BANKNOTES_SOURCE,
        "front_url": absolute("/Coins%20and%20Notes/Polymer/500/500obverse.jpg"),
        "back_url": absolute("/Coins%20and%20Notes/Polymer/500/500reverse.jpg"),
    },
    {
        "name": "1000菲律宾比索",
        "value": 1000,
        "years": "2022-present",
        "issued": "1000-piso polymer banknote, April 2022 circulation",
        "source": POLYMER_BANKNOTES_SOURCE,
        "front_url": absolute("/Coins%20and%20Notes/Polymer/1000/1000obverse.jpg"),
        "back_url": absolute("/Coins%20and%20Notes/Polymer/1000/1000reverse.jpg"),
    },
]


COINS = [
    {
        "name": "1菲律宾森蒂莫",
        "value": 0.01,
        "years": "2018-present",
        "issued": "26 March 2018",
        "source": NGC_COINS_SOURCE,
        "combined_url": absolute("/Coins%20and%20Notes/Coins/NGCCS/NGCCoins.png"),
        "front_box": (1810, 330, 1975, 515),
        "back_box": (1810, 525, 1975, 710),
    },
    {
        "name": "5菲律宾森蒂莫",
        "value": 0.05,
        "years": "2018-present",
        "issued": "26 March 2018",
        "source": NGC_COINS_SOURCE,
        "combined_url": absolute("/Coins%20and%20Notes/Coins/NGCCS/NGCCoins.png"),
        "front_box": (1615, 320, 1805, 515),
        "back_box": (1615, 525, 1805, 710),
    },
    {
        "name": "25菲律宾森蒂莫",
        "value": 0.25,
        "years": "2018-present",
        "issued": "26 March 2018",
        "source": NGC_COINS_SOURCE,
        "combined_url": absolute("/Coins%20and%20Notes/Coins/NGCCS/NGCCoins.png"),
        "front_box": (1415, 290, 1630, 515),
        "back_box": (1415, 525, 1630, 735),
    },
    {
        "name": "1菲律宾比索",
        "value": 1,
        "years": "2018-present",
        "issued": "26 March 2018",
        "source": NGC_COINS_SOURCE,
        "combined_url": absolute("/Coins%20and%20Notes/Coins/NGCCS/NGCCoins.png"),
        "front_box": (1180, 250, 1415, 515),
        "back_box": (1180, 525, 1415, 805),
    },
    {
        "name": "5菲律宾比索",
        "value": 5,
        "years": "2019-present",
        "issued": "17 December 2019 enhanced nine-sided 5-Piso coin",
        "source": NGC_COINS_SOURCE,
        "combined_url": absolute("/Coins%20and%20Notes/Coins/NGCCS/NGCCoins.png"),
        "front_box": (640, 230, 905, 515),
        "back_box": (640, 525, 905, 800),
    },
    {
        "name": "10菲律宾比索",
        "value": 10,
        "years": "2018-present",
        "issued": "26 March 2018",
        "source": NGC_COINS_SOURCE,
        "combined_url": absolute("/Coins%20and%20Notes/Coins/NGCCS/NGCCoins.png"),
        "front_box": (370, 220, 650, 515),
        "back_box": (370, 525, 650, 815),
    },
    {
        "name": "20菲律宾比索",
        "value": 20,
        "years": "2019-present",
        "issued": "17 December 2019",
        "source": NGC_COINS_SOURCE,
        "combined_url": absolute("/Coins%20and%20Notes/Coins/NGCCS/NGCCoins.png"),
        "front_box": (55, 195, 375, 515),
        "back_box": (55, 525, 375, 845),
    },
]


def main() -> int:
    if COUNTRY_DIR.exists():
        shutil.rmtree(COUNTRY_DIR)

    combined_coin_original = COUNTRY_DIR / "coin" / "combined_ngc_coins_original.png"
    download(COINS[0]["combined_url"], combined_coin_original)

    country_record = {
        "country": "菲律宾",
        "country_en": "Philippines",
        "name": "菲律宾比索",
        "name_en": "Philippine peso",
        "symbol": "₱",
        "code": "PHP",
        "source_policy": (
            "Bangko Sentral ng Pilipinas NGC banknote, First Philippine Polymer "
            "Banknote Series, and NGC coin pages were collected on 2026-07-04. "
            "For each denomination the latest available current-legal-tender design "
            "was selected: polymer banknotes for 50, 100, 500, and 1000 piso; enhanced "
            "NGC paper banknotes for 20 and 200 piso; NGC coins with the enhanced "
            "nine-sided 5-Piso coin and the 20-Piso coin."
        ),
        "coin": [make_coin(item, combined_coin_original) for item in COINS],
        "banknote": [make_banknote(item) for item in BANKNOTES],
    }

    currencies_path = ROOT / "currencies.json"
    currencies = json.loads(currencies_path.read_text(encoding="utf-8"))
    currencies = [record for record in currencies if record.get("code") != "PHP"]
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
            "source": "Bangko Sentral ng Pilipinas",
            "country": "Philippines",
            "collected_at": now,
            "coin_count": len(COINS),
            "banknote_count": len(BANKNOTES),
            "banknote_sources": [NGC_BANKNOTES_SOURCE, POLYMER_BANKNOTES_SOURCE],
            "coin_source": NGC_COINS_SOURCE,
            "sources": sorted({item["source"] for item in COINS + BANKNOTES}),
        }
    )
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
