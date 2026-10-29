#!/usr/bin/env python3
"""Add Chile CLP current banknotes and coins from Banco Central de Chile."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Chile"
IMAGE_INDEX_SOURCE = "https://www.billetesymonedas.cl/ZonaEducativa/ImagenesBilletesMonedas"
CURRENT_BANKNOTES_SOURCE = "https://www.billetesymonedas.cl/Billetes/BilleteActual/1000"
CURRENT_COINS_SOURCE = "https://www.billetesymonedas.cl/Monedas/Moneda/1"
BASE_IMAGE_URL = "https://www.billetesymonedas.cl/Documentos/ImagenesBilletesMonedas"


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


def make_item(item: dict[str, Any], kind: str) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / kind / item["name"]
    front_original = denomination_dir / "front_original.jpg"
    back_original = denomination_dir / "back_original.jpg"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["front_url"], front_original)
    download(item["back_url"], back_original)
    quality = normalize(front_original, back_original, front, back)
    return item_record(item, front, back, front_original, back_original, quality)


def banknote_url(value: int, side: str) -> str:
    return f"{BASE_IMAGE_URL}/BilletesActuales/%24{value}%20-%20{side}.jpg"


def coin_url(value: int, side: str) -> str:
    return f"{BASE_IMAGE_URL}/MonedasActuales/%24{value}%20-%20{side}.JPG"


BANKNOTES = [
    {
        "name": "1000智利比索",
        "value": 1000,
        "years": "2010-present",
        "issued": "2010",
        "source": CURRENT_BANKNOTES_SOURCE,
        "front_url": banknote_url(1000, "Anverso"),
        "back_url": banknote_url(1000, "Reverso"),
    },
    {
        "name": "2000智利比索",
        "value": 2000,
        "years": "2009-present",
        "issued": "2009",
        "source": "https://www.billetesymonedas.cl/Billetes/BilleteActual/2000",
        "front_url": banknote_url(2000, "Anverso"),
        "back_url": banknote_url(2000, "Reverso"),
    },
    {
        "name": "5000智利比索",
        "value": 5000,
        "years": "2009-present",
        "issued": "2009",
        "source": "https://www.billetesymonedas.cl/Billetes/BilleteActual/5000",
        "front_url": banknote_url(5000, "Anverso"),
        "back_url": banknote_url(5000, "Reverso"),
    },
    {
        "name": "10000智利比索",
        "value": 10000,
        "years": "2009-present",
        "issued": "2009",
        "source": "https://www.billetesymonedas.cl/Billetes/BilleteActual/10000",
        "front_url": banknote_url(10000, "Anverso"),
        "back_url": banknote_url(10000, "Reverso"),
    },
    {
        "name": "20000智利比索",
        "value": 20000,
        "years": "2009-present",
        "issued": "2009",
        "source": "https://www.billetesymonedas.cl/Billetes/BilleteActual/20000",
        "front_url": banknote_url(20000, "Anverso"),
        "back_url": banknote_url(20000, "Reverso"),
    },
]


COINS = [
    {
        "name": "10智利比索",
        "value": 10,
        "years": "current",
        "issued": "current",
        "source": CURRENT_COINS_SOURCE,
        "front_url": coin_url(10, "Cara"),
        "back_url": coin_url(10, "Sello"),
    },
    {
        "name": "50智利比索",
        "value": 50,
        "years": "current",
        "issued": "current",
        "source": CURRENT_COINS_SOURCE,
        "front_url": coin_url(50, "Cara"),
        "back_url": coin_url(50, "Sello"),
    },
    {
        "name": "100智利比索",
        "value": 100,
        "years": "2025 centenary legal-tender issue",
        "issued": "21 July 2025",
        "source": "https://www.billetesymonedas.cl/MonedaCentenario/Index",
        "front_url": coin_url(100, "Cara"),
        "back_url": coin_url(100, "Sello"),
    },
    {
        "name": "500智利比索",
        "value": 500,
        "years": "current",
        "issued": "current",
        "source": CURRENT_COINS_SOURCE,
        "front_url": coin_url(500, "Cara"),
        "back_url": coin_url(500, "Sello"),
    },
]


def main() -> None:
    banknotes = [make_item(item, "banknote") for item in BANKNOTES]
    coins = [make_item(item, "coin") for item in COINS]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text())
    country = {
        "country": "智利",
        "country_en": "Chile",
        "name": "智利比索",
        "name_en": "Chilean peso",
        "symbol": "$",
        "code": "CLP",
        "source_policy": (
            "Banco Central de Chile's Billetes y Monedas image index was used for "
            "current banknote and coin front/back images. One- and five-peso coins "
            "were omitted because Chile withdrew them from circulation in 2017."
        ),
        "coin": coins,
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("country_en") == "Chile"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text())
    log["chile"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "sources": [IMAGE_INDEX_SOURCE, CURRENT_BANKNOTES_SOURCE, CURRENT_COINS_SOURCE],
        "note": (
            "Current Chilean banknote and coin front/back images were downloaded from "
            "Banco Central de Chile's Billetes y Monedas image index."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
