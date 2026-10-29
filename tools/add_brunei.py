#!/usr/bin/env python3
"""Add verified current Brunei BND 2025-family banknotes from BDCB."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Brunei"
CIRCULATION_SOURCE = "https://www.bdcb.gov.bn/currency/circulation"
ANNOUNCEMENT_SOURCE = (
    "https://www.bdcb.gov.bn/publications/details?id=01k5sxez34r0m85rcdmrg63502"
)
BASE_IMAGE_URL = "https://www.bdcb.gov.bn/img/currency/circulation/2025"


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


def normalize(
    front_original: Path,
    back_original: Path,
    front: Path,
    back: Path,
) -> dict[str, Any]:
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
                "official PNGs flattened onto white and centered on a white canvas "
                "sized to max(front, back); JPEG quality 95"
            ),
        }


def image_url(value: int, side: str) -> str:
    filename = f"BND{value}.png" if side == "front" else f"back_BND{value}.png"
    return f"{BASE_IMAGE_URL}/{filename}"


BANKNOTES = [
    {
        "name": f"{value}文莱元",
        "value": value,
        "years": "2026-present",
        "issued": "2026",
        "front_url": image_url(value, "front"),
        "back_url": image_url(value, "back"),
    }
    for value in (1, 5, 10, 100, 500)
]


def make_item(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "banknote" / item["name"]
    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
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
        "source": CIRCULATION_SOURCE,
        "years": item["years"],
        "issued": item["issued"],
        "source_images": {"front": item["front_url"], "back": item["back_url"]},
        "original_front_image": front_original.relative_to(ROOT).as_posix(),
        "original_back_image": back_original.relative_to(ROOT).as_posix(),
        "original_source_images": {
            "front": item["front_url"],
            "back": item["back_url"],
        },
        "image_quality": quality,
    }


def main() -> None:
    banknotes = [make_item(item) for item in BANKNOTES]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    country = {
        "country": "文莱",
        "country_en": "Brunei",
        "name": "文莱元",
        "name_en": "Brunei dollar",
        "symbol": "$",
        "code": "BND",
        "source_policy": (
            "Brunei Darussalam Central Bank's official Currency in Circulation page "
            "was used for clean front/back PNGs of the five 2025-family banknotes. "
            "The official announcement scheduled circulation for the first half of "
            "2026, and the current circulation page now lists the family. Coins are "
            "left empty because the latest official coin image has SPECIMEN overlays; "
            "partial paper/coin coverage is permitted by policy."
        ),
        "coin": [],
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("code") == "BND"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text(encoding="utf-8"))
    log["brunei"] = {
        "status": "partial",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": 0,
        "banknotes": len(banknotes),
        "banknote_source": CIRCULATION_SOURCE,
        "sources": [CIRCULATION_SOURCE, ANNOUNCEMENT_SOURCE],
        "note": (
            "Downloaded clean official BDCB front/back PNGs for the five 2025-family "
            "banknotes now listed on the Currency in Circulation page. The annotated "
            "security-feature images and SPECIMEN-marked latest coin image were not "
            "used. No coins were added under the partial-coverage inclusion policy."
        ),
    }
    log_path.write_text(
        json.dumps(log, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
