#!/usr/bin/env python3
"""Add UAE AED current banknotes and coins from the Central Bank of the UAE."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "United_Arab_Emirates"
BASE_URL = "https://www.centralbank.ae"
CIRCULATED_CURRENCY_SOURCE = (
    f"{BASE_URL}/en/our-operations/currency-and-coins/circulated-currency/"
)


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
            "180",
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


def crop_content(image: Image.Image, threshold: int = 248, margin: int = 8) -> Image.Image:
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


def extension(url: str) -> str:
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".png"


def item_record(
    item: dict[str, Any],
    front: Path,
    back: Path,
    front_original: Path,
    back_original: Path,
    quality: dict[str, Any],
) -> dict[str, Any]:
    source_images = {
        "front": item.get("front_url", item.get("combined_url")),
        "back": item.get("back_url", item.get("combined_url")),
    }
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


def split_top_bottom(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    midpoint = image.height // 2
    return image.crop((0, 0, image.width, midpoint)), image.crop((0, midpoint, image.width, image.height))


def split_latest_right_column(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    midpoint_x = image.width // 2
    midpoint_y = image.height // 2
    front = image.crop((midpoint_x, 0, image.width, midpoint_y))
    back = image.crop((midpoint_x, midpoint_y, image.width, image.height))
    return front, back


def make_banknote(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "banknote" / item["name"]
    combined_ext = extension(item["combined_url"])
    combined_original = denomination_dir / f"combined_original{combined_ext}"
    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["combined_url"], combined_original)
    with Image.open(combined_original) as combined:
        if "crop_boxes" in item:
            front_crop = combined.crop(tuple(item["crop_boxes"]["front"]))
            back_crop = combined.crop(tuple(item["crop_boxes"]["back"]))
        elif item.get("split") == "latest_right_column":
            front_crop, back_crop = split_latest_right_column(combined)
        else:
            front_crop, back_crop = split_top_bottom(combined)

        crop_content(front_crop).save(front_original)
        crop_content(back_crop).save(back_original)

    quality = normalize(front_original, back_original, front, back)
    quality["source_split"] = item.get(
        "source_split",
        "Central Bank of the UAE official combined front/back banknote image split at the horizontal midpoint, then white border trimmed before normalization.",
    )
    record = item_record(item, front, back, front_original, back_original, quality)
    record["combined_original_image"] = combined_original.relative_to(ROOT).as_posix()
    record["combined_source_image"] = item["combined_url"]
    return record


def make_coin(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "coin" / item["name"]
    front_original = denomination_dir / f"front_original{extension(item['front_url'])}"
    back_original = denomination_dir / f"back_original{extension(item['back_url'])}"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["front_url"], front_original)
    download(item["back_url"], back_original)
    quality = normalize(front_original, back_original, front, back)
    return item_record(item, front, back, front_original, back_original, quality)


BANKNOTES = [
    {
        "name": "5阿联酋迪拉姆",
        "value": 5,
        "years": "2022-present polymer",
        "issued": "2022",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}current-banknotes/aed-5-polymer/",
        "combined_url": f"{BASE_URL}/media/vm5ida3a/aed-5-new-polymer-ar-en.png",
    },
    {
        "name": "10阿联酋迪拉姆",
        "value": 10,
        "years": "2022-present polymer",
        "issued": "2022",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}current-banknotes/aed-10-polymer/",
        "combined_url": f"{BASE_URL}/media/1hdnirga/aed-10-new-polymer-ar-en.png",
    },
    {
        "name": "20阿联酋迪拉姆",
        "value": 20,
        "years": "2015-present",
        "issued": "2015",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}current-banknotes/aed-20/",
        "combined_url": f"{BASE_URL}/media/pgxj5llt/aed-20-image-1.jpg",
        "crop_boxes": {
            "front": [500, 185, 1000, 392],
            "back": [500, 453, 1000, 649],
        },
        "source_split": (
            "Central Bank of the UAE official AED 20 image contains 1997 and 2015 "
            "front/back versions in a two-column layout; the right column was cropped "
            "as the latest 2015 issue, excluding the issue-year label, then white "
            "border trimmed before normalization."
        ),
    },
    {
        "name": "50阿联酋迪拉姆",
        "value": 50,
        "years": "2021-present polymer",
        "issued": "2021",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}current-banknotes/aed-50-polymer/",
        "combined_url": f"{BASE_URL}/media/ibdlm4w2/aed-50-newest-ar-en.png",
    },
    {
        "name": "100阿联酋迪拉姆",
        "value": 100,
        "years": "2025-present polymer",
        "issued": "2025",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}current-banknotes/aed-100-polymer/",
        "combined_url": f"{BASE_URL}/media/wacguu23/both-side-of-aed-banknote.jpg",
    },
    {
        "name": "200阿联酋迪拉姆",
        "value": 200,
        "years": "2016-present",
        "issued": "2016",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}current-banknotes/aed-200/",
        "combined_url": f"{BASE_URL}/media/fhzbtvzt/aed-200-image-2016.jpg",
        "crop_boxes": {
            "front": [180, 145, 820, 414],
            "back": [180, 443, 820, 709],
        },
        "source_split": (
            "Central Bank of the UAE official AED 200 latest-issue image contains "
            "front/back views separated by an issue-year label; the banknote areas "
            "were cropped directly, then white border trimmed before normalization."
        ),
    },
    {
        "name": "500阿联酋迪拉姆",
        "value": 500,
        "years": "2023-present polymer",
        "issued": "2023",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}current-banknotes/aed-500-polymer/",
        "combined_url": f"{BASE_URL}/media/vtih3tdx/500-both-side.jpg",
    },
    {
        "name": "1000阿联酋迪拉姆",
        "value": 1000,
        "years": "2022-present polymer",
        "issued": "2022",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}current-banknotes/aed-1000-polymer/",
        "combined_url": f"{BASE_URL}/media/efybw0d5/1000-bill.png",
    },
]


COINS = [
    {
        "name": "1阿联酋费尔",
        "value": 0.01,
        "years": "2005-present",
        "issued": "2005",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}coins/1-fils/",
        "front_url": f"{BASE_URL}/media/3hsdcm3s/_am1970.png",
        "back_url": f"{BASE_URL}/media/5yfhpjjf/_am1967.png",
    },
    {
        "name": "5阿联酋费尔",
        "value": 0.05,
        "years": "2001-present",
        "issued": "2001",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}coins/5-fils/",
        "front_url": f"{BASE_URL}/media/4dddrwbb/_am1964.png",
        "back_url": f"{BASE_URL}/media/5xjnyojz/_am1960.png",
    },
    {
        "name": "10阿联酋费尔",
        "value": 0.1,
        "years": "2011-present",
        "issued": "2011",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}coins/10-fils/",
        "front_url": f"{BASE_URL}/media/mnkdudif/_am1956.png",
        "back_url": f"{BASE_URL}/media/slpdoj4h/_am1954.png",
    },
    {
        "name": "25阿联酋费尔",
        "value": 0.25,
        "years": "2011-present",
        "issued": "2011",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}coins/25-fils/",
        "front_url": f"{BASE_URL}/media/vk0jm21m/_am1945a.png",
        "back_url": f"{BASE_URL}/media/dttb0sbg/_am1948a.png",
    },
    {
        "name": "50阿联酋费尔",
        "value": 0.5,
        "years": "2017-present",
        "issued": "2017",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}coins/50-fils/",
        "front_url": f"{BASE_URL}/media/rc0mrwps/_am1938.png",
        "back_url": f"{BASE_URL}/media/3zsjqwyb/_am1943.png",
    },
    {
        "name": "1阿联酋迪拉姆",
        "value": 1,
        "years": "2014-present",
        "issued": "2014",
        "source": f"{CIRCULATED_CURRENCY_SOURCE}coins/aed-1-coin/",
        "front_url": f"{BASE_URL}/media/znmpwkcd/_am32437.png",
        "back_url": f"{BASE_URL}/media/raegjgcf/_am32380.png",
    },
]


def main() -> int:
    banknotes = [make_banknote(item) for item in BANKNOTES]
    coins = [make_coin(item) for item in COINS]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text())
    country = {
        "country": "阿联酋",
        "country_en": "United Arab Emirates",
        "name": "阿联酋迪拉姆",
        "name_en": "United Arab Emirates dirham",
        "symbol": "د.إ",
        "code": "AED",
        "source_policy": (
            "Central Bank of the UAE circulated-currency pages were used. For each "
            "denomination, only the latest issue year listed by the official page was "
            "included; older designs for the same denomination were omitted."
        ),
        "coin": coins,
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("country_en") == "United Arab Emirates"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text())
    log["united_arab_emirates"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "source": CIRCULATED_CURRENCY_SOURCE,
        "sources": sorted({item["source"] for item in COINS + BANKNOTES}),
        "note": (
            "Banknotes were split from official Central Bank of the UAE combined "
            "front/back images. Coins were downloaded from official per-side PNGs. "
            "The AED 20 note image includes two issue columns; the 2015 right-column "
            "front/back images were cropped as the latest issue."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
