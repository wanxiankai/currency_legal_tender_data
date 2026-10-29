#!/usr/bin/env python3
"""Add verified current Qatar QAR banknotes from Qatar Central Bank."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Qatar"
CURRENT_BANKNOTES_SOURCE = "https://www.qcb.gov.qa/en/pages/currentbanknotes.aspx"
BASE_IMAGE_URL = "https://www.qcb.gov.qa/assets/img/banknotes"


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
                "official transparent PNGs flattened onto white and centered on a "
                "white canvas sized to max(front, back); JPEG quality 95"
            ),
        }


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
        "source": CURRENT_BANKNOTES_SOURCE,
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


def image_url(filename: str) -> str:
    return f"{BASE_IMAGE_URL}/{filename}"


BANKNOTES = [
    {
        "name": "1卡塔尔里亚尔",
        "value": 1,
        "years": "2026-present",
        "issued": "2026",
        "front_url": image_url("1RiyalFrontNew.PNG"),
        "back_url": image_url("1RiyalBackNew.PNG"),
    },
    {
        "name": "5卡塔尔里亚尔",
        "value": 5,
        "years": "2026-present",
        "issued": "2026",
        "front_url": image_url("05QR-front-2026.png"),
        "back_url": image_url("05QR-Back-2026.png"),
    },
    {
        "name": "10卡塔尔里亚尔",
        "value": 10,
        "years": "2026-present",
        "issued": "2026",
        "front_url": image_url("10QR-Front-2026.png"),
        "back_url": image_url("10QR-Back-2026.png"),
    },
    {
        "name": "50卡塔尔里亚尔",
        "value": 50,
        "years": "2026-present",
        "issued": "2026",
        "front_url": image_url("50QR-Front-2026.png"),
        "back_url": image_url("50QR-Back-2026.png"),
    },
    {
        "name": "100卡塔尔里亚尔",
        "value": 100,
        "years": "2020-present",
        "issued": "2020",
        "front_url": image_url("bn-100.png"),
        "back_url": image_url("bn-100-b.png"),
    },
    {
        "name": "200卡塔尔里亚尔",
        "value": 200,
        "years": "2020-present",
        "issued": "2020",
        "front_url": image_url("bn-200.png"),
        "back_url": image_url("bn-200-b.png"),
    },
    {
        "name": "500卡塔尔里亚尔",
        "value": 500,
        "years": "2020-present",
        "issued": "2020",
        "front_url": image_url("bn-500.png"),
        "back_url": image_url("bn-500-b.png"),
    },
]


def main() -> None:
    banknotes = [make_item(item) for item in BANKNOTES]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    country = {
        "country": "卡塔尔",
        "country_en": "Qatar",
        "name": "卡塔尔里亚尔",
        "name_en": "Qatari riyal",
        "symbol": "ر.ق",
        "code": "QAR",
        "source_policy": (
            "Qatar Central Bank's official Current Banknotes page was used for all "
            "seven banknote denominations with verified front/back PNGs. Coins are "
            "left empty because no comparable official circulation-coin front/back "
            "set was verified; partial paper/coin coverage is permitted by policy."
        ),
        "coin": [],
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("code") == "QAR"), None)
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
    log["qatar"] = {
        "status": "partial",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": 0,
        "banknotes": len(banknotes),
        "banknote_source": CURRENT_BANKNOTES_SOURCE,
        "sources": [CURRENT_BANKNOTES_SOURCE],
        "note": (
            "Downloaded official Qatar Central Bank front/back PNGs for all seven "
            "banknote denominations shown on the current-banknotes page. No coins "
            "were added in this pass under the partial-coverage inclusion policy."
        ),
    }
    log_path.write_text(
        json.dumps(log, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
