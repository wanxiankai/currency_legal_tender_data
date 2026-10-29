#!/usr/bin/env python3
"""Add Morocco MAD current 2023-series banknotes and coins from Bank Al-Maghrib."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Morocco"
BASE_URL = "https://www.bkam.ma"
BANKNOTES_SOURCE = (
    f"{BASE_URL}/en/Banknotes-and-coins/Cash-lifecycle/"
    "Banknotes-in-circulation/2023-series"
)
COINS_SOURCE = (
    f"{BASE_URL}/en/Banknotes-and-coins/Cash-lifecycle/"
    "Coins-in-circulation/2023-series"
)


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "curl",
            "--http1.1",
            "-L",
            "--fail",
            "--retry",
            "4",
            "--retry-delay",
            "4",
            "-A",
            "Mozilla/5.0",
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


def crop_content(image: Image.Image, threshold: int = 248, margin: int = 6) -> Image.Image:
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
        "Bank Al-Maghrib official 2023-series coin image contains obverse and "
        "reverse in one horizontal composite; it was split at the vertical "
        "midpoint, white border trimmed, then normalized."
    )
    record = item_record(item, front, back, front_original, back_original, quality)
    record["combined_original_image"] = combined_original.relative_to(ROOT).as_posix()
    record["combined_source_image"] = item["combined_url"]
    return record


BANKNOTES = [
    {
        "name": "20摩洛哥迪拉姆",
        "value": 20,
        "years": "2023-present series",
        "issued": "2023",
        "source": f"{BANKNOTES_SOURCE}/20-dh-banknote",
        "front_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/20dh-recto/"
            "9059307-1-fre-FR/20DH-RECTO_reference.jpg"
        ),
        "back_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/20dh-verso/"
            "9059311-1-fre-FR/20DH-VERSO_reference.jpg"
        ),
    },
    {
        "name": "50摩洛哥迪拉姆",
        "value": 50,
        "years": "2023-present series",
        "issued": "2023",
        "source": f"{BANKNOTES_SOURCE}/50-dh-banknote",
        "front_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/50dh-recto/"
            "9059347-1-fre-FR/50DH-RECTO_reference.jpg"
        ),
        "back_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/50dh-verso/"
            "9059351-1-fre-FR/50DH-VERSO_reference.jpg"
        ),
    },
    {
        "name": "100摩洛哥迪拉姆",
        "value": 100,
        "years": "2023-present series",
        "issued": "2023",
        "source": f"{BANKNOTES_SOURCE}/100-dh-banknote",
        "front_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/100dh-recto/"
            "9059362-1-fre-FR/100DH-RECTO_reference.jpg"
        ),
        "back_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/100dh-verso/"
            "9059366-1-fre-FR/100DH-VERSO_reference.jpg"
        ),
    },
    {
        "name": "200摩洛哥迪拉姆",
        "value": 200,
        "years": "2023-present series",
        "issued": "2023",
        "source": f"{BANKNOTES_SOURCE}/200-dh-banknote",
        "front_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/200dh-recto/"
            "9059381-1-fre-FR/200DH-RECTO_reference.jpg"
        ),
        "back_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/200dh-verso/"
            "9059385-1-fre-FR/200DH-VERSO_reference.jpg"
        ),
    },
]


COINS = [
    {
        "name": "10摩洛哥分",
        "value": 0.1,
        "years": "2023-present series",
        "issued": "2023",
        "source": f"{COINS_SOURCE}/10-centimes",
        "combined_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/10-centimes/"
            "9060595-1-fre-FR/10-Centimes.jpg"
        ),
    },
    {
        "name": "20摩洛哥分",
        "value": 0.2,
        "years": "2023-present series",
        "issued": "2023",
        "source": f"{COINS_SOURCE}/20-centimes",
        "combined_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/20-centimes/"
            "9060606-1-fre-FR/20-Centimes.jpg"
        ),
    },
    {
        "name": "半摩洛哥迪拉姆",
        "value": 0.5,
        "years": "2023-present series",
        "issued": "2023",
        "source": f"{COINS_SOURCE}/Dirham",
        "combined_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/1-2-dirham/"
            "9060617-1-fre-FR/1_2-Dirham.jpg"
        ),
    },
    {
        "name": "1摩洛哥迪拉姆",
        "value": 1,
        "years": "2023-present series",
        "issued": "2023",
        "source": f"{COINS_SOURCE}/1-dirham",
        "combined_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/1-dirham/"
            "9060841-1-fre-FR/1-Dirham.jpg"
        ),
    },
    {
        "name": "5摩洛哥迪拉姆",
        "value": 5,
        "years": "2023-present series",
        "issued": "2023",
        "source": f"{COINS_SOURCE}/5-dirhams",
        "combined_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/5-dirham/"
            "9060852-1-fre-FR/5-Dirham.jpg"
        ),
    },
    {
        "name": "10摩洛哥迪拉姆",
        "value": 10,
        "years": "2023-present series",
        "issued": "2023",
        "source": f"{COINS_SOURCE}/10-dirhams",
        "combined_url": (
            f"{BASE_URL}/var/bkam/storage/images/media/images/10-dirham/"
            "9060863-1-fre-FR/10-Dirham.jpg"
        ),
    },
]


def main() -> int:
    banknotes = [make_banknote(item) for item in BANKNOTES]
    coins = [make_coin(item) for item in COINS]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    country = {
        "country": "摩洛哥",
        "country_en": "Morocco",
        "name": "摩洛哥迪拉姆",
        "name_en": "Moroccan dirham",
        "symbol": "د.م.",
        "code": "MAD",
        "source_policy": (
            "Bank Al-Maghrib official 2023-series banknote and coin pages were "
            "used. Banknotes use official separate front/back reference images. "
            "Coins use official horizontal obverse/reverse composite images split "
            "into front/back originals."
        ),
        "coin": coins,
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("code") == "MAD"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text(encoding="utf-8"))
    log["morocco"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "banknote_source": BANKNOTES_SOURCE,
        "coin_source": COINS_SOURCE,
        "sources": [BANKNOTES_SOURCE, COINS_SOURCE],
        "note": (
            "Downloaded Bank Al-Maghrib 2023-series banknote front/back reference "
            "images. Downloaded 2023-series coin horizontal composite images and "
            "split them vertically into front/back originals before normalization."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
