#!/usr/bin/env python3
"""Add Taiwan TWD current banknotes and coins from the CBC Currency Museum."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Taiwan"
API_BASE = "https://museum.cbc.gov.tw/server/web"
IMAGE_BASE = "https://museum.cbc.gov.tw/ExhibitsImg/Search"
BANKNOTE_LIST_SOURCE = f"{API_BASE}/circulation_en/52"
COIN_LIST_SOURCE = f"{API_BASE}/circulation_en/54"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "curl",
            "-L",
            "--fail",
            "--retry",
            "3",
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


def fetch_json(url: str, dest: Path) -> Any:
    download(url, dest)
    return json.loads(dest.read_text())


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

        front.parent.mkdir(parents=True, exist_ok=True)
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
                "official PNG images flattened onto white, centered on white canvas sized "
                "to max(front, back) for the denomination/design; JPEG quality 95"
            ),
        }


def make_item(item: dict[str, Any], kind: str) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / kind / item["name"]
    detail_url = f"{API_BASE}/exhibits_en/{item['id']}"
    detail_path = ROOT / "tmp" / "taiwan_api" / f"{item['id']}.json"
    detail = fetch_json(detail_url, detail_path)
    images = detail["img"]
    if len(images) < 2:
        raise ValueError(f"{item['name']} does not have two images")

    # The museum API stores side order as front then back. One 2,000-dollar banknote
    # record labels both image types as front in text, but the second filename/name is the back.
    front_filename = images[0]["imgSrc"]
    back_filename = images[1]["imgSrc"]
    front_url = f"{IMAGE_BASE}/{front_filename}"
    back_url = f"{IMAGE_BASE}/{back_filename}"

    front_original = denomination_dir / "front_original.png"
    back_original = denomination_dir / "back_original.png"
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


BANKNOTES = [
    {
        "id": 43,
        "name": "100新台币",
        "value": 100,
        "years": "2001-present",
        "issued": "2 July 2001",
        "source": BANKNOTE_LIST_SOURCE,
    },
    {
        "id": 50,
        "name": "200新台币",
        "value": 200,
        "years": "2002-present",
        "issued": "2 January 2002",
        "source": BANKNOTE_LIST_SOURCE,
    },
    {
        "id": 52,
        "name": "500新台币",
        "value": 500,
        "years": "2005-present",
        "issued": "20 July 2005",
        "source": BANKNOTE_LIST_SOURCE,
    },
    {
        "id": 53,
        "name": "1000新台币",
        "value": 1000,
        "years": "2005-present",
        "issued": "20 July 2005",
        "source": BANKNOTE_LIST_SOURCE,
    },
    {
        "id": 51,
        "name": "2000新台币",
        "value": 2000,
        "years": "2002-present",
        "issued": "1 July 2002",
        "source": BANKNOTE_LIST_SOURCE,
    },
]


COINS = [
    {
        "id": 513,
        "name": "1新台币",
        "value": 1,
        "years": "1981-present",
        "issued": "8 December 1981",
        "source": COIN_LIST_SOURCE,
    },
    {
        "id": 514,
        "name": "5新台币",
        "value": 5,
        "years": "1981-present",
        "issued": "8 December 1981",
        "source": COIN_LIST_SOURCE,
    },
    {
        "id": 517,
        "name": "10新台币（蒋中正版）",
        "value": 10,
        "years": "1981-present",
        "issued": "8 December 1981",
        "source": COIN_LIST_SOURCE,
    },
    {
        "id": 316,
        "name": "10新台币（孙中山版）",
        "value": 10,
        "years": "2011-present",
        "issued": "11 January 2011",
        "source": COIN_LIST_SOURCE,
    },
    {
        "id": 62,
        "name": "20新台币",
        "value": 20,
        "years": "2001-present",
        "issued": "9 July 2001",
        "source": COIN_LIST_SOURCE,
    },
    {
        "id": 283,
        "name": "50新台币",
        "value": 50,
        "years": "2002-present",
        "issued": "26 April 2002",
        "source": COIN_LIST_SOURCE,
    },
]


def main() -> int:
    banknotes = [make_item(item, "banknote") for item in BANKNOTES]
    coins = [make_item(item, "coin") for item in COINS]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text())
    country = {
        "country": "台湾",
        "country_en": "Taiwan",
        "name": "新台币",
        "name_en": "New Taiwan dollar",
        "symbol": "NT$",
        "code": "TWD",
        "source_policy": (
            "Central Bank of the Republic of China (Taiwan) Currency Museum "
            "English circulation APIs were used. Current-circulation banknote "
            "records are from circulation_en/52, and current-circulation coin "
            "records are from circulation_en/54. The museum lists two current "
            "10-dollar coin designs; both are included as separate design entries."
        ),
        "coin": coins,
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("country_en") == "Taiwan"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text())
    log["taiwan"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "banknote_source": BANKNOTE_LIST_SOURCE,
        "coin_source": COIN_LIST_SOURCE,
        "sources": [BANKNOTE_LIST_SOURCE, COIN_LIST_SOURCE],
        "note": (
            "Downloaded official CBC Currency Museum detail records and front/back "
            "PNG images from /ExhibitsImg/Search/. Images were normalized to matching "
            "front/back dimensions per denomination/design."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
