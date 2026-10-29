#!/usr/bin/env python3
"""Add Kuwait KWD current banknotes and coins from the Central Bank of Kuwait."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Kuwait"
BASE_URL = "https://www.cbk.gov.kw"
BANKNOTES_SOURCE = f"{BASE_URL}/en/banknotes-and-coins/banknotes/sixth-issue"
COINS_SOURCE = f"{BASE_URL}/en/banknotes-and-coins/coins"


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


def extension(url: str) -> str:
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"


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


def make_banknote(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "banknote" / item["name"]
    front_original = denomination_dir / f"front_original{extension(item['front_url'])}"
    back_original = denomination_dir / f"back_original{extension(item['back_url'])}"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["front_url"], front_original)
    download(item["back_url"], back_original)
    quality = normalize(front_original, back_original, front, back)
    return item_record(item, front, back, front_original, back_original, quality)


def make_coin(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "coin" / item["name"]
    combined_original = denomination_dir / f"combined_original{extension(item['combined_url'])}"
    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["combined_url"], combined_original)
    with Image.open(combined_original) as combined:
        midpoint = combined.width // 2
        front_crop = combined.crop((0, 0, midpoint, combined.height))
        back_crop = combined.crop((midpoint, 0, combined.width, combined.height))
        crop_content(front_crop).save(front_original)
        crop_content(back_crop).save(back_original)

    quality = normalize(front_original, back_original, front, back)
    quality["source_split"] = (
        "Central Bank of Kuwait official 3x combined coin image split at the vertical "
        "midpoint, then transparent/white border trimmed before normalization."
    )
    record = item_record(item, front, back, front_original, back_original, quality)
    record["combined_original_image"] = combined_original.relative_to(ROOT).as_posix()
    record["combined_source_image"] = item["combined_url"]
    return record


BANKNOTES = [
    {
        "name": "1/4科威特第纳尔",
        "value": 0.25,
        "years": "2014-present sixth issue",
        "issued": "29 June 2014",
        "source": f"{BANKNOTES_SOURCE}/quarter-kd-note",
        "front_url": absolute("/en/images/detail-image-front-large-137667_v20_tcm10-137667.jpg"),
        "back_url": absolute("/en/images/detail-image-back-large-137663_v20_tcm10-137663.jpg"),
    },
    {
        "name": "1/2科威特第纳尔",
        "value": 0.5,
        "years": "2014-present sixth issue",
        "issued": "29 June 2014",
        "source": f"{BANKNOTES_SOURCE}/half-kd-note",
        "front_url": absolute("/en/images/detail-image-front-large-137601_v20_tcm10-137601.jpg"),
        "back_url": absolute("/en/images/detail-image-back-large-137597_v20_tcm10-137597.jpg"),
    },
    {
        "name": "1科威特第纳尔",
        "value": 1,
        "years": "2014-present sixth issue",
        "issued": "29 June 2014",
        "source": f"{BANKNOTES_SOURCE}/one-kd-note",
        "front_url": absolute("/en/images/detail-image-front-large-137337_v20_tcm10-137337.jpg"),
        "back_url": absolute("/en/images/detail-image-back-large-137333_v20_tcm10-137333.jpg"),
    },
    {
        "name": "5科威特第纳尔",
        "value": 5,
        "years": "2014-present sixth issue",
        "issued": "29 June 2014",
        "source": f"{BANKNOTES_SOURCE}/five-kd-note",
        "front_url": absolute("/en/images/detail-image-front-large-137535_v20_tcm10-137535.jpg"),
        "back_url": absolute("/en/images/detail-image-back-large-137531_v20_tcm10-137531.jpg"),
    },
    {
        "name": "10科威特第纳尔",
        "value": 10,
        "years": "2014-present sixth issue",
        "issued": "29 June 2014",
        "source": f"{BANKNOTES_SOURCE}/ten-kd-note",
        "front_url": absolute("/en/images/detail-image-front-large-137435_v30_tcm10-137435.jpg"),
        "back_url": absolute("/en/images/detail-image-back-large-137431_v30_tcm10-137431.jpg"),
    },
    {
        "name": "20科威特第纳尔",
        "value": 20,
        "years": "2014-present sixth issue",
        "issued": "29 June 2014",
        "source": f"{BANKNOTES_SOURCE}/twenty-kd-note",
        "front_url": absolute("/en/images/detail-image-front-large-137202_v40_tcm10-137202.jpg"),
        "back_url": absolute("/en/images/detail-image-back-large-137201_v40_tcm10-137201.jpg"),
    },
]


COINS = [
    {
        "name": "1科威特费尔",
        "value": 0.001,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "combined_url": absolute("/en/images/list-image-3x-140027_v30_tcm10-140027.png"),
    },
    {
        "name": "5科威特费尔",
        "value": 0.005,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "combined_url": absolute("/en/images/list-image-3x-140036_v20_tcm10-140036.png"),
    },
    {
        "name": "10科威特费尔",
        "value": 0.01,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "combined_url": absolute("/en/images/list-image-3x-140030_v20_tcm10-140030.png"),
    },
    {
        "name": "20科威特费尔",
        "value": 0.02,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "combined_url": absolute("/en/images/list-image-3x-140033_v20_tcm10-140033.png"),
    },
    {
        "name": "50科威特费尔",
        "value": 0.05,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "combined_url": absolute("/en/images/list-image-3x-137752_v40_tcm10-137752.png"),
    },
    {
        "name": "100科威特费尔",
        "value": 0.1,
        "years": "current circulation design",
        "issued": "current",
        "source": COINS_SOURCE,
        "combined_url": absolute("/en/images/list-image-3x-137736_v40_tcm10-137736.png"),
    },
]


def main() -> int:
    banknotes = [make_banknote(item) for item in BANKNOTES]
    coins = [make_coin(item) for item in COINS]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text())
    country = {
        "country": "科威特",
        "country_en": "Kuwait",
        "name": "科威特第纳尔",
        "name_en": "Kuwaiti dinar",
        "symbol": "د.ك",
        "code": "KWD",
        "source_policy": (
            "Central Bank of Kuwait official banknote and coin pages were used. "
            "Banknotes use the sixth issue released into circulation on 29 June 2014. "
            "Coins use the current coin page 3x official combined images."
        ),
        "coin": coins,
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("country_en") == "Kuwait"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text())
    log["kuwait"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "banknote_source": BANKNOTES_SOURCE,
        "coin_source": COINS_SOURCE,
        "sources": [BANKNOTES_SOURCE, COINS_SOURCE],
        "note": (
            "Downloaded CBK sixth-issue banknote large front/back images. "
            "Downloaded CBK current coin 3x combined side images and split each "
            "image vertically into front/back originals."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
