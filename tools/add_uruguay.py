#!/usr/bin/env python3
"""Add Uruguay UYU current banknotes and coins from Banco Central del Uruguay."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Uruguay"
BASE_URL = "https://subsitio.bcu.gub.uy"
BANKNOTES_SOURCE = f"{BASE_URL}/billetes/"
COINS_SOURCE = f"{BASE_URL}/monedas/"


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


def trim_banknote_crop(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    pixels = rgb.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = pixels[x, y]
            maximum = max(r, g, b)
            minimum = min(r, g, b)
            if maximum < 248 and maximum > 30 and (maximum - minimum > 8 or maximum < 220):
                xs.append(x)
                ys.append(y)
    if not xs or not ys:
        return rgb
    margin = 3
    box = (
        max(0, min(xs) - margin),
        max(0, min(ys) - margin),
        min(rgb.width, max(xs) + margin + 1),
        min(rgb.height, max(ys) + margin + 1),
    )
    return rgb.crop(box)


def split_banknote(combined_original: Path, front_original: Path, back_original: Path) -> None:
    with Image.open(combined_original) as image:
        rgb = flatten(image)
        midpoint = rgb.height // 2
        front_half = rgb.crop((0, 0, rgb.width, midpoint))
        back_half = rgb.crop((0, midpoint, rgb.width, rgb.height))
        trim_banknote_crop(front_half).save(front_original, "PNG")
        trim_banknote_crop(back_half).save(back_original, "PNG")


def normalize(front_original: Path, back_original: Path, front: Path, back: Path) -> dict[str, Any]:
    with Image.open(front_original) as front_image, Image.open(back_original) as back_image:
        front_rgb = flatten(front_image)
        back_rgb = flatten(back_image)
        final_width = max(front_rgb.width, back_rgb.width)
        final_height = max(front_rgb.height, back_rgb.height)

        def center(image: Image.Image) -> Image.Image:
            canvas = Image.new("RGB", (final_width, final_height), "white")
            canvas.paste(image, ((final_width - image.width) // 2, (final_height - image.height) // 2))
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
    source_images = {"front": item["front_url"], "back": item["back_url"]}
    if "combined_url" in item:
        source_images["combined"] = item["combined_url"]
    return {
        "name": item["name"],
        "value": item["value"],
        "front_view_image": front.relative_to(ROOT).as_posix(),
        "back_view_image": back.relative_to(ROOT).as_posix(),
        "source": item["source"],
        "years": item["years"],
        "issued": item["issued"],
        "source_images": source_images,
        "original_front_image": front_original.relative_to(ROOT).as_posix(),
        "original_back_image": back_original.relative_to(ROOT).as_posix(),
        "original_source_images": source_images,
        "image_quality": quality,
    }


def make_coin(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "coin" / item["name"]
    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["front_url"], front_original)
    download(item["back_url"], back_original)
    quality = normalize(front_original, back_original, front, back)
    return item_record(item, front, back, front_original, back_original, quality)


def make_banknote(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "banknote" / item["name"]
    combined_original = denomination_dir / "combined_original.png"
    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["combined_url"], combined_original)
    split_banknote(combined_original, front_original, back_original)
    item["front_url"] = item["combined_url"]
    item["back_url"] = item["combined_url"]
    quality = normalize(front_original, back_original, front, back)
    quality["combined_original_width"] = Image.open(combined_original).width
    quality["combined_original_height"] = Image.open(combined_original).height
    quality["transform"] = (
        "BCU combined front/back display image split into upper/lower halves, "
        "trimmed to each banknote image, flattened onto white, and normalized "
        "to matching front/back canvas; JPEG quality 95"
    )
    return item_record(item, front, back, front_original, back_original, quality)


def upload(path: str) -> str:
    return f"{BASE_URL}/wp-content/uploads/{path}"


COINS = [
    {
        "name": "1乌拉圭比索",
        "value": 1,
        "years": "BCU current coin page, latest tab 2024",
        "issued": "2024",
        "source": COINS_SOURCE,
        "front_url": upload("2025/05/1a.png"),
        "back_url": upload("2025/05/1r.png"),
    },
    {
        "name": "2乌拉圭比索",
        "value": 2,
        "years": "BCU current coin page, latest listed circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "front_url": upload("2025/05/2a.png"),
        "back_url": upload("2025/05/2r.png"),
    },
    {
        "name": "5乌拉圭比索",
        "value": 5,
        "years": "BCU current coin page, latest listed circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "front_url": upload("2025/05/5a.png"),
        "back_url": upload("2025/05/5r.png"),
    },
    {
        "name": "10乌拉圭比索",
        "value": 10,
        "years": "BCU current coin page, latest listed circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "front_url": upload("2025/05/10a.png"),
        "back_url": upload("2025/05/10r.png"),
    },
]


BANKNOTES = [
    {
        "name": "20乌拉圭比索",
        "value": 20,
        "years": "2020-present polymer series A/B",
        "issued": "2020",
        "source": BANKNOTES_SOURCE,
        "combined_url": upload("2026/06/20-AB-POLI%CC%81MERO.png"),
    },
    {
        "name": "50乌拉圭比索",
        "value": 50,
        "years": "2022-present polymer series A",
        "issued": "2022",
        "source": BANKNOTES_SOURCE,
        "combined_url": upload("2026/06/50-A-POLIMERO.png"),
    },
    {
        "name": "100乌拉圭比索",
        "value": 100,
        "years": "2019-present series G/H",
        "issued": "2019",
        "source": BANKNOTES_SOURCE,
        "combined_url": upload("2026/06/100-GH.png"),
    },
    {
        "name": "200乌拉圭比索",
        "value": 200,
        "years": "2021-present series F/G",
        "issued": "2021",
        "source": BANKNOTES_SOURCE,
        "combined_url": upload("2026/06/200-FG.png"),
    },
    {
        "name": "500乌拉圭比索",
        "value": 500,
        "years": "2019-present series E/F/G",
        "issued": "2019",
        "source": BANKNOTES_SOURCE,
        "combined_url": upload("2026/06/500-EFG.png"),
    },
    {
        "name": "1000乌拉圭比索",
        "value": 1000,
        "years": "2019-present series E/F/G",
        "issued": "2019",
        "source": BANKNOTES_SOURCE,
        "combined_url": upload("2026/06/1000-EFG.png"),
    },
    {
        "name": "2000乌拉圭比索",
        "value": 2000,
        "years": "2020-present series B/C/D",
        "issued": "2020",
        "source": BANKNOTES_SOURCE,
        "combined_url": upload("2026/06/2000-BCD.png"),
    },
]


def main() -> None:
    coins = [make_coin(item) for item in COINS]
    banknotes = [make_banknote(item) for item in BANKNOTES]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text())
    country = {
        "country": "乌拉圭",
        "country_en": "Uruguay",
        "name": "乌拉圭比索",
        "name_en": "Uruguayan peso",
        "symbol": "$U",
        "code": "UYU",
        "source_policy": (
            "Banco Central del Uruguay's banknote and coin subsites were used. "
            "Coin entries use the official current coin page display images. "
            "Banknote entries use BCU combined front/back display images, split "
            "into front and back images for this dataset."
        ),
        "coin": coins,
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("country_en") == "Uruguay"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text())
    log["uruguay"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "sources": [BANKNOTES_SOURCE, COINS_SOURCE],
        "note": (
            "Current Uruguay coin images and BCU banknote combined display images "
            "were downloaded from Banco Central del Uruguay subsites."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
