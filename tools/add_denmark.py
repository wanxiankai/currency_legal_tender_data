#!/usr/bin/env python3
"""Add Denmark DKK current legal-tender banknotes and coins from Danmarks Nationalbank."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Denmark"
BASE_URL = "https://www.nationalbanken.dk"
BANKNOTES_SOURCE = (
    "https://www.nationalbanken.dk/en/what-we-do/notes-and-coins/"
    "danish-banknotes-today"
)
COINS_SOURCE = (
    "https://www.nationalbanken.dk/en/what-we-do/notes-and-coins/"
    "danish-coins-today"
)
PRESS_PHOTOS_SOURCE = (
    "https://www.nationalbanken.dk/en/news-and-knowledge/press/press-photos"
)


def absolute(path: str) -> str:
    return path if path.startswith("http") else f"{BASE_URL}{path}"


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
            "90",
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


def crop_content(image: Image.Image, threshold: int = 248, margin: int = 4) -> Image.Image:
    rgb = flatten(image)
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


def item_record(
    item: dict[str, Any],
    front: Path,
    back: Path,
    front_original: Path,
    back_original: Path,
    quality: dict[str, Any],
) -> dict[str, Any]:
    source_url = absolute(item["source_image"])
    return {
        "name": item["name"],
        "value": item["value"],
        "front_view_image": front.relative_to(ROOT).as_posix(),
        "back_view_image": back.relative_to(ROOT).as_posix(),
        "source": item["source"],
        "years": item["years"],
        "issued": item["issued"],
        "source_images": {"front": source_url, "back": source_url},
        "original_front_image": front_original.relative_to(ROOT).as_posix(),
        "original_back_image": back_original.relative_to(ROOT).as_posix(),
        "original_source_images": {"front": source_url, "back": source_url},
        "image_quality": quality,
    }


def make_split_item(item: dict[str, Any], kind: str, split_axis: str) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / kind / item["name"]
    combined_original = denomination_dir / "combined_original.png"
    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(absolute(item["source_image"]), combined_original)
    with Image.open(combined_original) as combined:
        if split_axis == "horizontal":
            midpoint = combined.height // 2
            front_crop = combined.crop((0, 0, combined.width, midpoint))
            back_crop = combined.crop((0, midpoint, combined.width, combined.height))
        elif split_axis == "vertical":
            midpoint = combined.width // 2
            front_crop = combined.crop((0, 0, midpoint, combined.height))
            back_crop = combined.crop((midpoint, 0, combined.width, combined.height))
        else:
            raise ValueError(f"Unknown split axis: {split_axis}")

        crop_content(front_crop).save(front_original)
        crop_content(back_crop).save(back_original)

    quality = normalize(front_original, back_original, front, back)
    record = item_record(item, front, back, front_original, back_original, quality)
    record["combined_original_image"] = combined_original.relative_to(ROOT).as_posix()
    record["combined_source_image"] = absolute(item["source_image"])
    record["image_quality"]["source_split"] = (
        f"Danmarks Nationalbank official combined {kind} image split on the "
        f"{split_axis} midpoint, then white border trimmed before normalization."
    )
    return record


BANKNOTES = [
    {
        "name": "50丹麦克朗",
        "value": 50,
        "years": "2009A, 2026-present",
        "issued": "February 2026",
        "source": BANKNOTES_SOURCE,
        "source_image": "/media/3qmnzfp1/2009a-seddelserie-50kr.png",
    },
    {
        "name": "100丹麦克朗",
        "value": 100,
        "years": "2009A, 2024-present",
        "issued": "February 2024",
        "source": BANKNOTES_SOURCE,
        "source_image": "/media/rrplhbpz/2009a-seddelserie-100kr.png",
    },
    {
        "name": "200丹麦克朗",
        "value": 200,
        "years": "2009A, 2024-present",
        "issued": "February 2024",
        "source": BANKNOTES_SOURCE,
        "source_image": "/media/nxlf3s5q/2009a-seddelserie-200kr.png",
    },
    {
        "name": "500丹麦克朗",
        "value": 500,
        "years": "2009A, 2020-present",
        "issued": "November 2020",
        "source": BANKNOTES_SOURCE,
        "source_image": "/media/yurncwyo/2009a-seddelserie-500kr.png",
    },
]


COINS = [
    {
        "name": "50丹麦欧尔",
        "value": 0.5,
        "years": "2023-present",
        "issued": "2023",
        "source": COINS_SOURCE,
        "source_image": "/media/lfjbnidp/cirkulationsmoenter-2023-50ore.png",
    },
    {
        "name": "1丹麦克朗",
        "value": 1,
        "years": "2025-present",
        "issued": "December 2025",
        "source": COINS_SOURCE,
        "source_image": "/media/yavb1bui/cirkulationsmoenter-2025-1kr.png",
    },
    {
        "name": "2丹麦克朗",
        "value": 2,
        "years": "2025-present",
        "issued": "December 2025",
        "source": COINS_SOURCE,
        "source_image": "/media/uhihgfnn/cirkulationsmoenter-2025-2kr.png",
    },
    {
        "name": "5丹麦克朗",
        "value": 5,
        "years": "2025-present",
        "issued": "December 2025",
        "source": COINS_SOURCE,
        "source_image": "/media/2kdljrmm/cirkulationsmoenter-2025-5kr.png",
    },
    {
        "name": "10丹麦克朗",
        "value": 10,
        "years": "2025-present",
        "issued": "December 2025",
        "source": COINS_SOURCE,
        "source_image": "/media/amrlhaf1/cirkulationsmoenter-2025-10kr.png",
    },
    {
        "name": "20丹麦克朗",
        "value": 20,
        "years": "2025-present",
        "issued": "December 2025",
        "source": COINS_SOURCE,
        "source_image": "/media/xntb2dam/cirkulationsmoenter-2025-20kr.png",
    },
]


def main() -> None:
    banknotes = [make_split_item(item, "banknote", "horizontal") for item in BANKNOTES]
    coins = [make_split_item(item, "coin", "vertical") for item in COINS]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text())
    country = {
        "country": "丹麦",
        "country_en": "Denmark",
        "name": "丹麦克朗",
        "name_en": "Danish krone",
        "symbol": "kr.",
        "code": "DKK",
        "source_policy": (
            "Danmarks Nationalbank official pages and press photos were used. "
            "Only banknotes valid after the 1000-krone/older-series withdrawal "
            "and current coin-sequence denominations were included."
        ),
        "coin": coins,
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("country_en") == "Denmark"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text())
    log["denmark"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "sources": [BANKNOTES_SOURCE, COINS_SOURCE, PRESS_PHOTOS_SOURCE],
        "note": (
            "Banknotes were split from official 2009A combined front/back PNGs. "
            "Coins were split from official combined front/back PNGs."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
