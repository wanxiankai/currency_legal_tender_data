#!/usr/bin/env python3
"""Add Georgia GEL current banknotes and coins from the National Bank of Georgia."""

from __future__ import annotations

import json
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Georgia"
BASE_URL = "https://nbg.gov.ge"
MEDIA_BASE = f"{BASE_URL}/fm"
BANKNOTES_SOURCE = f"{BASE_URL}/en/georgian-money/banknotes"
COINS_SOURCE = f"{BASE_URL}/en/georgian-money/coins"


def media_url(path: str) -> str:
    return f"{MEDIA_BASE}/{urllib.parse.quote(path, safe='/')}"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "curl",
            "-L",
            "--fail",
            "--retry",
            "2",
            "--connect-timeout",
            "20",
            "--max-time",
            "120",
            "-A",
            (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
            ),
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
                "to max(front, back) for the denomination/design; JPEG quality 95"
            ),
        }


def extension(url: str) -> str:
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".png"


def make_item(item: dict[str, Any], kind: str) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / kind / item["name"]
    front_url = media_url(item["front_path"])
    back_url = media_url(item["back_path"])
    front_original = denomination_dir / f"front_original{extension(front_url)}"
    back_original = denomination_dir / f"back_original{extension(back_url)}"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(front_url, front_original)
    download(back_url, back_original)
    quality = normalize(front_original, back_original, front, back)
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


BANKNOTE_PREFIX = "მონეტები_და_ბანკნოტები/მიმოქცევის_მონეტები"

BANKNOTES = [
    {
        "name": "5格鲁吉亚拉里",
        "value": 5,
        "years": "2017-present upgraded series",
        "issued": "1 September 2017",
        "source": BANKNOTES_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/5gel-front.png",
        "back_path": f"{BANKNOTE_PREFIX}/5gel-back.png",
    },
    {
        "name": "10格鲁吉亚拉里",
        "value": 10,
        "years": "2019-present upgraded series",
        "issued": "1 October 2019",
        "source": BANKNOTES_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/10gel-front.png",
        "back_path": f"{BANKNOTE_PREFIX}/10gel-back.png",
    },
    {
        "name": "20格鲁吉亚拉里",
        "value": 20,
        "years": "2016-present upgraded series",
        "issued": "1 February 2016",
        "source": BANKNOTES_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/54a5088e20gel-front-1.png",
        "back_path": f"{BANKNOTE_PREFIX}/20gel-back-1.png",
    },
    {
        "name": "50格鲁吉亚拉里",
        "value": 50,
        "years": "2016-present upgraded series",
        "issued": "1 February 2016",
        "source": BANKNOTES_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/51c7046550gel-front-1.png",
        "back_path": f"{BANKNOTE_PREFIX}/50gel-back-1.png",
    },
    {
        "name": "100格鲁吉亚拉里",
        "value": 100,
        "years": "2016-present upgraded series",
        "issued": "1 November 2016",
        "source": BANKNOTES_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/100gel-front-1.png",
        "back_path": f"{BANKNOTE_PREFIX}/100gel-back-1.png",
    },
]


COINS = [
    {
        "name": "5格鲁吉亚特瑞",
        "value": 0.05,
        "years": "1995-present",
        "issued": "1995",
        "source": COINS_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/5t-1.png",
        "back_path": f"{BANKNOTE_PREFIX}/1993.png",
    },
    {
        "name": "10格鲁吉亚特瑞",
        "value": 0.1,
        "years": "1995-present",
        "issued": "1995",
        "source": COINS_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/10t-1.png",
        "back_path": f"{BANKNOTE_PREFIX}/1993.png",
    },
    {
        "name": "20格鲁吉亚特瑞",
        "value": 0.2,
        "years": "1995-present",
        "issued": "1995",
        "source": COINS_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/20t.png",
        "back_path": f"{BANKNOTE_PREFIX}/1993.png",
    },
    {
        "name": "50格鲁吉亚特瑞",
        "value": 0.5,
        "years": "2006-present",
        "issued": "2006",
        "source": COINS_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/50t-2.png",
        "back_path": f"{BANKNOTE_PREFIX}/50t-back-1.png",
    },
    {
        "name": "1格鲁吉亚拉里",
        "value": 1,
        "years": "2006-present",
        "issued": "2006",
        "source": COINS_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/1gel-1.png",
        "back_path": f"{BANKNOTE_PREFIX}/1gel-back-1.png",
    },
    {
        "name": "2格鲁吉亚拉里",
        "value": 2,
        "years": "2006-present",
        "issued": "2006",
        "source": COINS_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/2gel-2.png",
        "back_path": f"{BANKNOTE_PREFIX}/2gel-back-1.png",
    },
    {
        "name": "10格鲁吉亚拉里（基督诞生版）",
        "value": 10,
        "years": "2000-present",
        "issued": "2000",
        "source": COINS_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/10gel2-00000-00000.png",
        "back_path": f"{BANKNOTE_PREFIX}/10gel2back-00000.png",
    },
    {
        "name": "10格鲁吉亚拉里（格鲁吉亚国家版）",
        "value": 10,
        "years": "2000-present",
        "issued": "2000",
        "source": COINS_SOURCE,
        "front_path": f"{BANKNOTE_PREFIX}/10gel-00000.png",
        "back_path": f"{BANKNOTE_PREFIX}/10gelback-00000-00000.png",
    },
]


def main() -> int:
    banknotes = [make_item(item, "banknote") for item in BANKNOTES]
    coins = [make_item(item, "coin") for item in COINS]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text())
    country = {
        "country": "格鲁吉亚",
        "country_en": "Georgia",
        "name": "格鲁吉亚拉里",
        "name_en": "Georgian lari",
        "symbol": "₾",
        "code": "GEL",
        "source_policy": (
            "National Bank of Georgia banknote and coin pages were used. Banknotes "
            "include the current upgraded series listed under banknotes issued since "
            "2016. Coins include NBG circulation-coin page entries with complete "
            "front/back images, including the two listed 10-lari circulating designs."
        ),
        "coin": coins,
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("country_en") == "Georgia"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text())
    log["georgia"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "banknote_source": BANKNOTES_SOURCE,
        "coin_source": COINS_SOURCE,
        "sources": [BANKNOTES_SOURCE, COINS_SOURCE],
        "note": (
            "Downloaded National Bank of Georgia current banknote and circulation-coin "
            "front/back image files referenced in the Next.js page data."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
