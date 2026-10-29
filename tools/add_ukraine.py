#!/usr/bin/env python3
"""Add Ukraine UAH current/legal-tender banknotes and coins from the NBU."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Ukraine"
BASE_URL = "https://bank.gov.ua"
BANKNOTES_SOURCE = f"{BASE_URL}/en/uah/obig-banknote"
COINS_SOURCE = f"{BASE_URL}/en/uah/obig-coin"
UAH_SOURCE = f"{BASE_URL}/en/uah"


def asset_url(path: str) -> str:
    return f"{BASE_URL}{path}"


def extension(url: str) -> str:
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".png"


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
                "official NBU images flattened onto white, centered on white canvas sized "
                "to max(front, back) for the denomination; JPEG quality 95"
            ),
        }


def make_item(item: dict[str, Any], kind: str) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / kind / item["name"]
    front_url = asset_url(item["front_path"])
    back_url = asset_url(item["back_path"])
    front_original = denomination_dir / f"front_original{extension(front_url)}"
    back_original = denomination_dir / f"back_original{extension(back_url)}"
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
        "name": "20乌克兰格里夫纳",
        "value": 20,
        "years": "2018 design, 2023 print date; current fourth-generation banknote",
        "issued": "24 October 2023",
        "source": BANKNOTES_SOURCE,
        "front_path": "/admin_uploads/banknote/c00bf88d78e3111c8f48c767750e5b43.jpeg",
        "back_path": "/admin_uploads/banknote/1fc06628272aa210ba98b12fcc63d265.jpeg",
    },
    {
        "name": "50乌克兰格里夫纳",
        "value": 50,
        "years": "2019 design, 2021 print date; current fourth-generation banknote",
        "issued": "21 December 2021",
        "source": BANKNOTES_SOURCE,
        "front_path": "/admin_uploads/banknote/8680aced1aa585b07a03449a7f60b5b8.jpeg",
        "back_path": "/admin_uploads/banknote/33d2b0504fb4ce9e5a9c16d19496c7ea.jpeg",
    },
    {
        "name": "100乌克兰格里夫纳",
        "value": 100,
        "years": "2014 design, 2022 print date; current fourth-generation banknote",
        "issued": "19 December 2022",
        "source": BANKNOTES_SOURCE,
        "front_path": "/admin_uploads/banknote/ee85a8dfafcfdf0aa9f889f5683e5441.png",
        "back_path": "/admin_uploads/banknote/33688ecad1462e362ce0d67f4c779be6.png",
    },
    {
        "name": "200乌克兰格里夫纳",
        "value": 200,
        "years": "2019 design, 2021 print date; current fourth-generation banknote",
        "issued": "9 November 2021",
        "source": BANKNOTES_SOURCE,
        "front_path": "/admin_uploads/banknote/97bb906b3e327e90de243321010245db.jpeg",
        "back_path": "/admin_uploads/banknote/7e8dd9ffb8853fd3be65c7ffc90e7022.jpeg",
    },
    {
        "name": "500乌克兰格里夫纳",
        "value": 500,
        "years": "2015 design, 2023 print date; current fourth-generation banknote",
        "issued": "25 April 2023",
        "source": BANKNOTES_SOURCE,
        "front_path": "/admin_uploads/banknote/00bded1ca8c6d781a0f58d9a44874fc7.jpeg",
        "back_path": "/admin_uploads/banknote/27eb6eb75126cfce2f1a3c2993e184b0.jpeg",
    },
    {
        "name": "1000乌克兰格里夫纳",
        "value": 1000,
        "years": "2019 design, 2023 print date; current fourth-generation banknote",
        "issued": "20 July 2023",
        "source": BANKNOTES_SOURCE,
        "front_path": "/admin_uploads/banknote/80fa5505775d09204888b7542ffaba3c.jpeg",
        "back_path": "/admin_uploads/banknote/09a7a9f2b37cd27b1b1a332820056c03.jpeg",
    },
]


COINS = [
    {
        "name": "1乌克兰戈比",
        "value": 0.01,
        "years": "1996 design; legal tender indefinitely, no longer actively produced",
        "issued": "2 September 1996",
        "source": f"{BASE_URL}/en/uah/obig-coin/1_1996?single",
        "front_path": "/admin_uploads/coin/4cf1c59d0d7cbbdccef9c8f8df363dd2.png",
        "back_path": "/admin_uploads/coin/9bf787849354793e61a7a7d696cbcd11.png",
    },
    {
        "name": "2乌克兰戈比",
        "value": 0.02,
        "years": "1996 design; legal tender indefinitely, no longer actively produced",
        "issued": "2 September 1996",
        "source": f"{BASE_URL}/en/uah/obig-coin/2_1996?single",
        "front_path": "/admin_uploads/coin/555239cb732492fc150d33469c9583d8.png",
        "back_path": "/admin_uploads/coin/31b2baa8b1198d450d1c86a49f5495cf.png",
    },
    {
        "name": "5乌克兰戈比",
        "value": 0.05,
        "years": "1996 design; legal tender indefinitely, no longer actively produced",
        "issued": "2 September 1996",
        "source": f"{BASE_URL}/en/uah/obig-coin/5_1996?single",
        "front_path": "/admin_uploads/coin/0cc3e3c94c68c1e915d23f2dfc3da104.png",
        "back_path": "/admin_uploads/coin/e4dc9143f0d309b52125ff60c43ed060.png",
    },
    {
        "name": "10乌克兰戈比",
        "value": 0.1,
        "years": "2014 design; legal tender, being gradually withdrawn since 1 October 2025",
        "issued": "1 September 2014",
        "source": f"{BASE_URL}/en/uah/obig-coin/10_2016?single",
        "front_path": "/admin_uploads/coin/b9554e394f930eb1b6f34d988f46dc2e.jpeg",
        "back_path": "/admin_uploads/coin/a1f2f6e2200b60d0e079015b336c0df6.jpeg",
    },
    {
        "name": "25乌克兰戈比",
        "value": 0.25,
        "years": "1996 design; legal tender indefinitely, no longer actively produced",
        "issued": "2 September 1996",
        "source": f"{BASE_URL}/en/uah/obig-coin/25_1996?single",
        "front_path": "/admin_uploads/coin/d205e0279c1bb14ed997eca084a2ce91.png",
        "back_path": "/admin_uploads/coin/3d468a7600b7abbb0daebc4bd6319349.png",
    },
    {
        "name": "50乌克兰戈比",
        "value": 0.5,
        "years": "2013 design; 2026 listed among years of coinage",
        "issued": "1 October 2013",
        "source": COINS_SOURCE,
        "front_path": "/admin_uploads/coin/99b45b7e2a51708cf5907b8fa76fcace.png",
        "back_path": "/admin_uploads/coin/c907b6d487e0a2500b27ece2131c6edb.png",
    },
    {
        "name": "1乌克兰格里夫纳",
        "value": 1,
        "years": "2018 design; 2026 listed among years of coinage",
        "issued": "27 April 2018",
        "source": COINS_SOURCE,
        "front_path": "/admin_uploads/coin/05e88148cdf38027b48a3dc65a9a7dd3.png",
        "back_path": "/admin_uploads/coin/c0c503245b6e11adb881a7505260360c.png",
    },
    {
        "name": "2乌克兰格里夫纳",
        "value": 2,
        "years": "2018 design; 2026 listed among years of coinage",
        "issued": "27 April 2018",
        "source": COINS_SOURCE,
        "front_path": "/admin_uploads/coin/16c665e8f9007c12a4ff368de9f833a5.png",
        "back_path": "/admin_uploads/coin/176e2009c681db30c073a8f9a81cbb3f.png",
    },
    {
        "name": "5乌克兰格里夫纳",
        "value": 5,
        "years": "2018 design; 2026 listed among years of coinage",
        "issued": "20 December 2019",
        "source": COINS_SOURCE,
        "front_path": "/admin_uploads/coin/f40c13ca8e84656bf5d45d5035cdd716.png",
        "back_path": "/admin_uploads/coin/15f8631d6813d46db9a42b5637781327.png",
    },
    {
        "name": "10乌克兰格里夫纳",
        "value": 10,
        "years": "2018 design; 2026 listed among years of coinage",
        "issued": "3 June 2020",
        "source": COINS_SOURCE,
        "front_path": "/admin_uploads/coin/8ae42bc2ededb34878253a9bd372ee4b.png",
        "back_path": "/admin_uploads/coin/589b9c257cc8e11d0334dc43f5388336.png",
    },
]


def main() -> int:
    banknotes = [make_item(item, "banknote") for item in BANKNOTES]
    coins = [make_item(item, "coin") for item in COINS]

    country = {
        "country": "乌克兰",
        "country_en": "Ukraine",
        "name": "乌克兰格里夫纳",
        "name_en": "Ukrainian hryvnia",
        "symbol": "₴",
        "code": "UAH",
        "source_policy": (
            "National Bank of Ukraine current banknote and coin pages were used. "
            "Fourth-generation current banknotes of 20, 50, 100, 200, 500, and "
            "1,000 hryvnias are included; 1-, 2-, 5-, and 10-hryvnia banknotes "
            "ceased to be legal tender on 2 March 2026 and are omitted. Current "
            "1-, 2-, 5-, and 10-hryvnia coins plus 50-kopiika coins are included. "
            "The 10-kopiika coin is included because the NBU states it is still "
            "legal tender while being gradually withdrawn from 1 October 2025. "
            "The 1-, 2-, 5-, and 25-kopiika coins are included because the NBU "
            "states they remain legal tender indefinitely."
        ),
        "coin": coins,
        "banknote": banknotes,
    }

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text())
    index = next((i for i, item in enumerate(data) if item.get("country_en") == "Ukraine"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text())
    log["ukraine"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "banknote_source": BANKNOTES_SOURCE,
        "coin_source": COINS_SOURCE,
        "sources": [UAH_SOURCE, BANKNOTES_SOURCE, COINS_SOURCE],
        "note": (
            "Downloaded official National Bank of Ukraine front/back images for "
            "current fourth-generation banknotes and legal-tender coins. Images "
            "were normalized to matching front/back dimensions per denomination."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
