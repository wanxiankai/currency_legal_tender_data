#!/usr/bin/env python3
"""Add Switzerland CHF current banknotes and coins from official sources."""

from __future__ import annotations

import json
import shutil
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Switzerland"
SNB_SERIES_9_SOURCE = "https://www.snb.ch/en/the-snb/mandates-goals/cash/series-9"
SWISSMINT_COINS_SOURCE = "https://www.swissmint.ch/en/circulation-coins"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        dest.write_bytes(response.read())


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
    front_url = item.get("front_url", item.get("combined_url"))
    back_url = item.get("back_url", item.get("combined_url"))
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


def make_banknote(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "banknote" / item["name"]
    front_original = denomination_dir / "front_original.jpg"
    back_original = denomination_dir / "back_original.jpg"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["front_url"], front_original)
    download(item["back_url"], back_original)
    quality = normalize(front_original, back_original, front, back)

    return item_record(item, front, back, front_original, back_original, quality)


def make_coin(item: dict[str, Any]) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / "coin" / item["name"]
    combined_original = denomination_dir / "combined_original.jpg"
    front_original = denomination_dir / "front_original.jpg"
    back_original = denomination_dir / "back_original.jpg"
    front = denomination_dir / "front.jpg"
    back = denomination_dir / "back.jpg"

    download(item["combined_url"], combined_original)
    with Image.open(combined_original) as combined:
        midpoint = combined.width // 2
        combined.crop((0, 0, midpoint, combined.height)).save(front_original, "JPEG", quality=95)
        combined.crop((midpoint, 0, combined.width, combined.height)).save(back_original, "JPEG", quality=95)

    quality = normalize(front_original, back_original, front, back)
    record = item_record(item, front, back, front_original, back_original, quality)
    record["combined_original_image"] = combined_original.relative_to(ROOT).as_posix()
    record["combined_source_image"] = item["combined_url"]
    record["image_quality"]["coin_split"] = (
        "Swissmint official front/back combined coin image split at the horizontal "
        "midpoint; left half treated as front, right half treated as back."
    )
    return record


BANKNOTES = [
    {
        "name": "10瑞士法郎",
        "value": 10,
        "years": "2017-present",
        "issued": "18 October 2017",
        "source": SNB_SERIES_9_SOURCE,
        "front_url": "https://www.snb.ch/.imaging/flex/jcr:479322ac-79a8-406a-a2e3-ec45b4c9c739/hash/326420f732f7c422b8901b7999899f7f/mode/BOUNDED/ratio/827:1455/version/1527781594/width/900/banknote_widget_series_9_design_denomination_10_front.n.jpg",
        "back_url": "https://www.snb.ch/.imaging/flex/jcr:9483b488-7f8b-43b7-b806-17fee5c9b2ab/hash/19485e9b469c0d60d66533cbc59eb4f4/mode/BOUNDED/ratio/827:1455/version/1527781586/width/900/banknote_widget_series_9_design_denomination_10_back.n.jpg",
    },
    {
        "name": "20瑞士法郎",
        "value": 20,
        "years": "2017-present",
        "issued": "17 May 2017",
        "source": SNB_SERIES_9_SOURCE,
        "front_url": "https://www.snb.ch/.imaging/flex/jcr:0c9038c8-be4c-43f3-b725-07fa476a2adb/hash/af21ea85d57d9677414bf7856ee14841/mode/BOUNDED/ratio/827:1538/version/1527781617/width/900/banknote_widget_series_9_design_denomination_20_front.n.jpg",
        "back_url": "https://www.snb.ch/.imaging/flex/jcr:767b1a30-bef7-4970-9d9d-7b62aad44b85/hash/b5780f5e6e01990dd5d2a89d9ae1a58d/mode/BOUNDED/ratio/827:1535/version/1527781608/width/900/banknote_widget_series_9_design_denomination_20_back.n.jpg",
    },
    {
        "name": "50瑞士法郎",
        "value": 50,
        "years": "2016-present",
        "issued": "12 April 2016",
        "source": SNB_SERIES_9_SOURCE,
        "front_url": "https://www.snb.ch/.imaging/flex/jcr:9f40e3d8-b83d-4715-9655-50239a6e13db/hash/122fc88c80465c6d739b01848a7149c6/mode/BOUNDED/ratio/827:1626/version/1527781644/width/900/banknote_widget_series_9_design_denomination_50_front.n.jpg",
        "back_url": "https://www.snb.ch/.imaging/flex/jcr:c0f0005f-46b5-42f2-8be1-e92b3148d4d9/hash/f6d987fa4506bb421eb10a0ac50bbf05/mode/BOUNDED/ratio/827:1620/version/1527781634/width/900/banknote_widget_series_9_design_denomination_50_back.n.jpg",
    },
    {
        "name": "100瑞士法郎",
        "value": 100,
        "years": "2019-present",
        "issued": "12 September 2019",
        "source": SNB_SERIES_9_SOURCE,
        "front_url": "https://www.snb.ch/.imaging/flex/jcr:2452788b-acc7-43c9-bf84-efe417b1e5e5/hash/f8b510f60aad9e1e9b31b780b7d67435/mode/BOUNDED/ratio/827:1701/version/1567497600/width/900/banknote_widget_series_9_design_denomination_100_front.n.jpg",
        "back_url": "https://www.snb.ch/.imaging/flex/jcr:b5d6014b-ca2c-4617-842a-7eaa6e333b0c/hash/94c267829b475f79ae5750ca1b0aa406/mode/BOUNDED/ratio/827:1701/version/1567497600/width/900/banknote_widget_series_9_design_denomination_100_back.n.jpg",
    },
    {
        "name": "200瑞士法郎",
        "value": 200,
        "years": "2018-present",
        "issued": "22 August 2018",
        "source": SNB_SERIES_9_SOURCE,
        "front_url": "https://www.snb.ch/.imaging/flex/jcr:e14782aa-f6e9-4f04-a84f-fc97503ab663/hash/f56b6dec6f3a6d56c1a308b76d7dac7d/mode/BOUNDED/ratio/827:1788/version/1534320000/width/900/banknote_widget_series_9_design_denomination_200_front.n.jpg",
        "back_url": "https://www.snb.ch/.imaging/flex/jcr:3406de9a-f254-4b95-8b5a-de4ac12f6c94/hash/36f6d4a648fd388b8572b09bb0ec5ac7/mode/BOUNDED/ratio/827:1789/version/1534320000/width/900/banknote_widget_series_9_design_denomination_200_back.n.jpg",
    },
    {
        "name": "1000瑞士法郎",
        "value": 1000,
        "years": "2019-present",
        "issued": "13 March 2019",
        "source": SNB_SERIES_9_SOURCE,
        "front_url": "https://www.snb.ch/.imaging/flex/jcr:778b68b3-1344-4872-93d7-ed4e1b01acb7/hash/d700300c83c5ba0e78786083115e1d1b/mode/BOUNDED/ratio/827:1866/version/1551776400/width/900/banknote_widget_series_9_design_denomination_1000_front.n.jpg",
        "back_url": "https://www.snb.ch/.imaging/flex/jcr:0b7471d0-76f0-4c69-b9a6-c7d46b40869f/hash/b98ef1361819c62bce979f097cd5b87f/mode/BOUNDED/ratio/827:1866/version/1551776400/width/900/banknote_widget_series_9_design_denomination_1000_back.n.jpg",
    },
]


COINS = [
    {
        "name": "5瑞士生丁",
        "value": 0.05,
        "years": "current circulation",
        "issued": "current circulation coin listed by Swissmint",
        "source": SWISSMINT_COINS_SOURCE,
        "combined_url": "https://prod-swissmintch-hcms-sdweb.imgix.net/dam/en/sd-web/-YAWW6PnOV1R/5-rappen-425x120px.jpg?auto=format&w=4096",
    },
    {
        "name": "10瑞士生丁",
        "value": 0.1,
        "years": "current circulation",
        "issued": "current circulation coin listed by Swissmint",
        "source": SWISSMINT_COINS_SOURCE,
        "combined_url": "https://prod-swissmintch-hcms-sdweb.imgix.net/dam/en/sd-web/MNrG50YvlEqx/10-rappen-425x133px.jpg?auto=format&w=4096",
    },
    {
        "name": "20瑞士生丁",
        "value": 0.2,
        "years": "current circulation",
        "issued": "current circulation coin listed by Swissmint",
        "source": SWISSMINT_COINS_SOURCE,
        "combined_url": "https://prod-swissmintch-hcms-sdweb.imgix.net/dam/en/sd-web/ajyuxXZFiIPx/20-rappen-425x146px.jpg?auto=format&w=4096",
    },
    {
        "name": "50瑞士生丁",
        "value": 0.5,
        "years": "current circulation",
        "issued": "current circulation coin listed by Swissmint",
        "source": SWISSMINT_COINS_SOURCE,
        "combined_url": "https://prod-swissmintch-hcms-sdweb.imgix.net/dam/en/sd-web/AJKJXBRa5txQ/50-rappen-425x126px.jpg?auto=format&w=4096",
    },
    {
        "name": "1瑞士法郎",
        "value": 1,
        "years": "current circulation",
        "issued": "current circulation coin listed by Swissmint",
        "source": SWISSMINT_COINS_SOURCE,
        "combined_url": "https://prod-swissmintch-hcms-sdweb.imgix.net/dam/en/sd-web/m75OXjGbYcNK/1-franken-425x159px.jpg?auto=format&w=4096",
    },
    {
        "name": "2瑞士法郎",
        "value": 2,
        "years": "current circulation",
        "issued": "current circulation coin listed by Swissmint",
        "source": SWISSMINT_COINS_SOURCE,
        "combined_url": "https://prod-swissmintch-hcms-sdweb.imgix.net/dam/en/sd-web/N4k8NgrgDR48/2-franken-425x186px.jpg?auto=format&w=4096",
    },
    {
        "name": "5瑞士法郎",
        "value": 5,
        "years": "current circulation",
        "issued": "current circulation coin listed by Swissmint",
        "source": SWISSMINT_COINS_SOURCE,
        "combined_url": "https://prod-swissmintch-hcms-sdweb.imgix.net/dam/en/sd-web/Z6811vWPIblY/5-franken-425x213px.jpg?auto=format&w=4096",
    },
]


def main() -> int:
    if COUNTRY_DIR.exists():
        shutil.rmtree(COUNTRY_DIR)

    country_record = {
        "country": "瑞士",
        "country_en": "Switzerland",
        "name": "瑞士法郎",
        "name_en": "Swiss franc",
        "symbol": "Fr.",
        "code": "CHF",
        "source_policy": (
            "Swiss National Bank ninth-series banknote page and Swissmint circulation "
            "coin page were collected on 2026-07-04. SNB series 9 is the current "
            "issued banknote series under this collection scope; Swissmint circulation "
            "coin page lists the included current standard coin denominations."
        ),
        "coin": [make_coin(item) for item in COINS],
        "banknote": [make_banknote(item) for item in BANKNOTES],
    }

    currencies_path = ROOT / "currencies.json"
    currencies = json.loads(currencies_path.read_text(encoding="utf-8"))
    currencies = [record for record in currencies if record.get("code") != "CHF"]
    currencies.append(country_record)
    currencies_path.write_text(
        json.dumps(currencies, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    log["generated_at"] = now
    log.setdefault("runs", []).append(
        {
            "source": "Swiss National Bank and Swissmint",
            "country": "Switzerland",
            "collected_at": now,
            "coin_count": len(COINS),
            "banknote_count": len(BANKNOTES),
            "banknote_source": SNB_SERIES_9_SOURCE,
            "coin_source": SWISSMINT_COINS_SOURCE,
            "sources": sorted({item["source"] for item in COINS + BANKNOTES}),
        }
    )
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
