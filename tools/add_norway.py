#!/usr/bin/env python3
"""Add Norway NOK legal tender notes and coins from Norges Bank."""

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
COUNTRY_DIR = ROOT / "Norway"
BASE_URL = "https://www.norges-bank.no"
LEGAL_TENDER_SOURCE = (
    "https://www.norges-bank.no/en/topics/notes-and-coins/legal-tender-notes-coins/"
)


def absolute(path: str) -> str:
    return urllib.parse.urljoin(BASE_URL, path)


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


def extension_from_url(url: str) -> str:
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"


def normalize(front_original: Path, back_original: Path, front: Path, back: Path) -> dict[str, Any]:
    with Image.open(front_original) as front_image, Image.open(back_original) as back_image:
        front_rgb = front_image.convert("RGB")
        back_rgb = back_image.convert("RGB")
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
            "front_original_width": front_rgb.width,
            "front_original_height": front_rgb.height,
            "back_original_width": back_rgb.width,
            "back_original_height": back_rgb.height,
            "normalized_same_size": True,
            "transform": (
                "original images centered on white canvas sized to max(front, back) "
                "for the denomination; JPEG quality 95"
            ),
        }


def make_item(item: dict[str, Any], kind: str) -> dict[str, Any]:
    denomination_dir = COUNTRY_DIR / kind / item["name"]
    front_url = absolute(item["front_path"])
    back_url = absolute(item["back_path"])
    front_original = denomination_dir / f"front_original{extension_from_url(front_url)}"
    back_original = denomination_dir / f"back_original{extension_from_url(back_url)}"
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
        "name": "50挪威克朗",
        "value": 50,
        "years": "2018-present",
        "issued": "18 October 2018",
        "source": "https://www.norges-bank.no/en/topics/notes-and-coins/legal-tender-notes-coins/50-krone-note/",
        "front_path": "/contentassets/eb814597ebb2476a962ba65632445030/50front_viii_specimen.jpg?v=24022026090737&mode=crop&width=800",
        "back_path": "/contentassets/c512480665b74c2aa8a16838f4001175/50back_viii_specimen.jpg?v=24022026090814&mode=crop&width=800",
    },
    {
        "name": "100挪威克朗",
        "value": 100,
        "years": "2017-present",
        "issued": "30 May 2017",
        "source": "https://www.norges-bank.no/en/topics/notes-and-coins/legal-tender-notes-coins/100-krone-note/",
        "front_path": "/contentassets/af09e2c1bc39400ea8637df900c36ba7/100front_viii_specimen.jpg?v=24022026104245&mode=crop&width=800",
        "back_path": "/contentassets/b035f0210ab14556a929fe104350bc54/100back_viii_specimen.jpg?v=24022026104312&mode=crop&width=800",
    },
    {
        "name": "200挪威克朗",
        "value": 200,
        "years": "2017-present",
        "issued": "30 May 2017",
        "source": "https://www.norges-bank.no/en/topics/notes-and-coins/legal-tender-notes-coins/200-krone-note/",
        "front_path": "/contentassets/17c5319dddb84bd98555698a6b6fcd1e/200front_viii_specimen.jpg?v=24022026104558&mode=crop&width=800",
        "back_path": "/contentassets/a6756f40bb444362a73bf936054aa1ae/200back_viii_specimen.jpg?v=24022026104617&mode=crop&width=800",
    },
    {
        "name": "500挪威克朗",
        "value": 500,
        "years": "2018-present",
        "issued": "18 October 2018",
        "source": "https://www.norges-bank.no/en/topics/notes-and-coins/legal-tender-notes-coins/500-krone-note/",
        "front_path": "/contentassets/5cd10153600a41be9c5a4c86171304c4/500front_viii_specimen.jpg?v=24022026104842&mode=crop&width=800",
        "back_path": "/contentassets/340b96a04ef64f20b25c8ed1331c1eb5/500back_viii_specimen.jpg?v=24022026104919&mode=crop&width=800",
    },
    {
        "name": "1000挪威克朗",
        "value": 1000,
        "years": "2019-present",
        "issued": "14 November 2019",
        "source": "https://www.norges-bank.no/en/topics/notes-and-coins/legal-tender-notes-coins/1000-krone-note/",
        "front_path": "/contentassets/76f94e07b2ba4d539832ba0c82423c25/1000f_specimen.jpg?v=24022026105325&mode=crop&width=800",
        "back_path": "/contentassets/b22eec5ac2f8457eb8c2279c04a57a16/1000b_specimen.jpg?v=24022026105344&mode=crop&width=800",
    },
]


COINS = [
    {
        "name": "1挪威克朗",
        "value": 1,
        "years": "2016-present",
        "issued": "2016",
        "source": "https://www.norges-bank.no/en/topics/notes-and-coins/legal-tender-notes-coins/1-krone-coin/",
        "front_path": "/contentassets/44b32055e3f64b2082e42cd9e550320b/2016-kors-1-kr.jpg?v=18082025145514",
        "back_path": "/contentassets/44b32055e3f64b2082e42cd9e550320b/2016-fugl-1-kr.jpg?v=18082025145509",
    },
    {
        "name": "5挪威克朗",
        "value": 5,
        "years": "2008-present",
        "issued": "2008",
        "source": "https://www.norges-bank.no/en/topics/notes-and-coins/legal-tender-notes-coins/5-krone-coin/",
        "front_path": "/contentassets/df9d6b7501934d70889fd6b3f3add013/2008-kjede-5-kr.jpg?v=18082025145614",
        "back_path": "/contentassets/df9d6b7501934d70889fd6b3f3add013/2008-akantus-5-kr.jpg?v=18082025145622",
    },
    {
        "name": "10挪威克朗",
        "value": 10,
        "years": "2007-present",
        "issued": "2007",
        "source": "https://www.norges-bank.no/en/topics/notes-and-coins/legal-tender-notes-coins/10-krone-coin/",
        "front_path": "/contentassets/eb050e69fe294cb7884c3e5053847688/2007-konge-10-kr.jpg?v=18082025145412",
        "back_path": "/contentassets/eb050e69fe294cb7884c3e5053847688/2007-stavkirke-10-kr.jpg?v=18082025145419",
    },
    {
        "name": "20挪威克朗",
        "value": 20,
        "years": "2003-present",
        "issued": "2003",
        "source": "https://www.norges-bank.no/en/topics/notes-and-coins/legal-tender-notes-coins/20-krone-coin/",
        "front_path": "/contentassets/54c6b50aee4345daa6233ce6eb13cc19/2003-konge-20-kr.jpg?v=18082025145141",
        "back_path": "/contentassets/54c6b50aee4345daa6233ce6eb13cc19/2003-oseberg-20-kr.jpg?v=18082025145144",
    },
]


def main() -> int:
    if COUNTRY_DIR.exists():
        shutil.rmtree(COUNTRY_DIR)

    country_record = {
        "country": "挪威",
        "country_en": "Norway",
        "name": "挪威克朗",
        "name_en": "Norwegian krone",
        "symbol": "kr",
        "code": "NOK",
        "source_policy": (
            "Norges Bank legal tender notes and coins pages were collected on "
            "2026-07-04. The legal tender page lists the included current standard "
            "circulation banknotes and coins; individual denomination pages provide "
            "front and back images."
        ),
        "coin": [make_item(item, "coin") for item in COINS],
        "banknote": [make_item(item, "banknote") for item in BANKNOTES],
    }

    currencies_path = ROOT / "currencies.json"
    currencies = json.loads(currencies_path.read_text(encoding="utf-8"))
    currencies = [record for record in currencies if record.get("code") != "NOK"]
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
            "source": "Norges Bank",
            "country": "Norway",
            "collected_at": now,
            "coin_count": len(COINS),
            "banknote_count": len(BANKNOTES),
            "legal_tender_source": LEGAL_TENDER_SOURCE,
            "sources": sorted({item["source"] for item in COINS + BANKNOTES}),
        }
    )
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
