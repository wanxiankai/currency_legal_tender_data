#!/usr/bin/env python3
"""Add Bahrain BHD current banknotes and coins from the Central Bank of Bahrain."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Bahrain"
BASE_URL = "https://www.cbb.gov.bh"
BANKNOTES_SOURCE = f"{BASE_URL}/upgraded-fourth-issue/"
COINS_SOURCE = f"{BASE_URL}/current-coins/"


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
                "to max(front, back) for the denomination; JPEG quality 95"
            ),
        }


def extension(url: str) -> str:
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"


def make_item(item: dict[str, Any], kind: str) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / kind / item["name"]
    front_original = denomination_dir / f"front_original{extension(item['front_url'])}"
    back_original = denomination_dir / f"back_original{extension(item['back_url'])}"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["front_url"], front_original)
    download(item["back_url"], back_original)
    quality = normalize(front_original, back_original, front, back)
    return {
        "name": item["name"],
        "value": item["value"],
        "front_view_image": front.relative_to(ROOT).as_posix(),
        "back_view_image": back.relative_to(ROOT).as_posix(),
        "source": item["source"],
        "years": item["years"],
        "issued": item["issued"],
        "source_images": {"front": item["front_url"], "back": item["back_url"]},
        "original_front_image": front_original.relative_to(ROOT).as_posix(),
        "original_back_image": back_original.relative_to(ROOT).as_posix(),
        "original_source_images": {"front": item["front_url"], "back": item["back_url"]},
        "image_quality": quality,
    }


BANKNOTES = [
    {
        "name": "1/2巴林第纳尔",
        "value": 0.5,
        "years": "2023 upgraded fourth issue",
        "issued": "2023",
        "source": BANKNOTES_SOURCE,
        "front_url": f"{BASE_URL}/wp-content/uploads/2023/04/half-1-UPDATED-scaled.jpg",
        "back_url": f"{BASE_URL}/wp-content/uploads/2023/04/half-2-UPDATED-2-scaled.jpg",
    },
    {
        "name": "1巴林第纳尔",
        "value": 1,
        "years": "2023 upgraded fourth issue",
        "issued": "2023",
        "source": BANKNOTES_SOURCE,
        "front_url": f"{BASE_URL}/wp-content/uploads/2023/04/1-1-UPDATED-scaled.jpg",
        "back_url": f"{BASE_URL}/wp-content/uploads/2023/04/1-2-UPDATED-scaled.jpg",
    },
    {
        "name": "5巴林第纳尔",
        "value": 5,
        "years": "2023 upgraded fourth issue",
        "issued": "2023",
        "source": BANKNOTES_SOURCE,
        "front_url": f"{BASE_URL}/wp-content/uploads/2023/04/5-1-UPDATED-scaled.jpg",
        "back_url": f"{BASE_URL}/wp-content/uploads/2023/04/5-2-UPDATED-scaled.jpg",
    },
    {
        "name": "10巴林第纳尔",
        "value": 10,
        "years": "2023 upgraded fourth issue",
        "issued": "2023",
        "source": BANKNOTES_SOURCE,
        "front_url": f"{BASE_URL}/wp-content/uploads/2023/04/10-1-UPDATED-scaled.jpg",
        "back_url": f"{BASE_URL}/wp-content/uploads/2023/04/10-2-UPDATED-scaled.jpg",
    },
    {
        "name": "20巴林第纳尔",
        "value": 20,
        "years": "2023 upgraded fourth issue",
        "issued": "2023",
        "source": BANKNOTES_SOURCE,
        "front_url": f"{BASE_URL}/wp-content/uploads/2023/04/20-1-UPDATED-scaled.jpg",
        "back_url": f"{BASE_URL}/wp-content/uploads/2023/04/20-2-UPDATED-scaled.jpg",
    },
]


COINS = [
    {
        "name": "5巴林费尔",
        "value": 0.005,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "front_url": f"{BASE_URL}/wp-content/uploads/2019/01/5-fils-obverse.jpg",
        "back_url": f"{BASE_URL}/wp-content/uploads/2019/01/5-fils-reverse.jpg",
    },
    {
        "name": "10巴林费尔",
        "value": 0.01,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "front_url": f"{BASE_URL}/wp-content/uploads/2019/01/10-fils-Obverse.jpg",
        "back_url": f"{BASE_URL}/wp-content/uploads/2019/01/10-fils-reverse.jpg",
    },
    {
        "name": "25巴林费尔",
        "value": 0.025,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "front_url": f"{BASE_URL}/wp-content/uploads/2019/01/25-fils-obverse.jpg",
        "back_url": f"{BASE_URL}/wp-content/uploads/2019/01/25-fils-reverse.jpg",
    },
    {
        "name": "50巴林费尔",
        "value": 0.05,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "front_url": f"{BASE_URL}/wp-content/uploads/2019/01/50-fils-Obverse.jpg",
        "back_url": f"{BASE_URL}/wp-content/uploads/2019/01/50-fils-Reverse.jpg",
    },
    {
        "name": "100巴林费尔",
        "value": 0.1,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "front_url": f"{BASE_URL}/wp-content/uploads/2019/01/100-fils-Obverse.jpg",
        "back_url": f"{BASE_URL}/wp-content/uploads/2019/01/100-fils-Reverse.jpg",
    },
]


def main() -> int:
    banknotes = [make_item(item, "banknote") for item in BANKNOTES]
    coins = [make_item(item, "coin") for item in COINS]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text())
    country = {
        "country": "巴林",
        "country_en": "Bahrain",
        "name": "巴林第纳尔",
        "name_en": "Bahraini dinar",
        "symbol": ".د.ب",
        "code": "BHD",
        "source_policy": (
            "Central Bank of Bahrain current currency pages were used. Banknotes "
            "use the 2023 upgraded fourth issue images. Coins use the designs listed "
            "on the CBB Current Coins page; no older banknote issue pages were included."
        ),
        "coin": coins,
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("country_en") == "Bahrain"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text())
    log["bahrain"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "banknote_source": BANKNOTES_SOURCE,
        "coin_source": COINS_SOURCE,
        "sources": [BANKNOTES_SOURCE, COINS_SOURCE],
        "note": (
            "Downloaded CBB 2023 upgraded fourth issue banknote front/back images "
            "and current coin front/back images. WordPress original coin image URLs "
            "were used where the page displayed thumbnail variants."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
