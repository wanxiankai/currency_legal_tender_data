#!/usr/bin/env python3
"""Add Costa Rica CRC current banknotes and circulating coin designs from BCCR."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
COUNTRY_DIR = ROOT / "Costa_Rica"
BASE_URL = "https://www.bccr.fi.cr"
BANKNOTES_SOURCE = f"{BASE_URL}/billetes-y-monedas/billetes-en-circulaci%C3%B3n"
COINS_SOURCE = f"{BASE_URL}/billetes-y-monedas/monedas"


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
                "to max(front, back) for the denomination/design; JPEG quality 95"
            ),
        }


def source_url(path: str) -> str:
    return path if path.startswith("http") else f"{BASE_URL}{path}"


def extension(path: str) -> str:
    suffix = Path(path.split("?", 1)[0]).suffix.lower()
    return ".png" if suffix == ".png" else ".jpg"


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
        "name": "1000哥斯达黎加科朗",
        "value": 1000,
        "years": "2021-present polymer series C",
        "issued": "15 October 2021",
        "source": BANKNOTES_SOURCE,
        "front_url": source_url("/billetes-y-monedas/billetes_circulacion/01_1000C-A.jpg"),
        "back_url": source_url("/billetes-y-monedas/billetes_circulacion/01_1000C-R.jpg"),
    },
    {
        "name": "2000哥斯达黎加科朗",
        "value": 2000,
        "years": "2020-present polymer series B",
        "issued": "1 December 2020",
        "source": BANKNOTES_SOURCE,
        "front_url": source_url("/billetes-y-monedas/billetes_circulacion/2000_anverso_polimero.jpg"),
        "back_url": source_url("/billetes-y-monedas/billetes_circulacion/2000_reverso_polimero.jpg"),
    },
    {
        "name": "5000哥斯达黎加科朗",
        "value": 5000,
        "years": "2020-present polymer series C",
        "issued": "1 December 2020",
        "source": BANKNOTES_SOURCE,
        "front_url": source_url("/billetes-y-monedas/billetes_circulacion/5000_anverso_polimero.jpg"),
        "back_url": source_url("/billetes-y-monedas/billetes_circulacion/5000_reverso_polimero.jpg"),
    },
    {
        "name": "10000哥斯达黎加科朗",
        "value": 10000,
        "years": "2021-present polymer series B",
        "issued": "15 October 2021",
        "source": BANKNOTES_SOURCE,
        "front_url": source_url("/billetes-y-monedas/billetes_circulacion/10mil-polimero-anverso.PNG"),
        "back_url": source_url("/billetes-y-monedas/billetes_circulacion/10mil-polimero-reverso.PNG"),
    },
    {
        "name": "20000哥斯达黎加科朗",
        "value": 20000,
        "years": "2020-present polymer series B",
        "issued": "26 November 2020",
        "source": BANKNOTES_SOURCE,
        "front_url": source_url("/billetes-y-monedas/billetes_circulacion/20_mil_anverso_polimero.jpg"),
        "back_url": source_url("/billetes-y-monedas/billetes_circulacion/20_mil_reverso_polimero.jpg"),
    },
]


def coin(name: str, value: int, front: str, back: str, years: str = "current circulation design") -> dict[str, Any]:
    return {
        "name": name,
        "value": value,
        "years": years,
        "issued": "current",
        "source": COINS_SOURCE,
        "front_url": source_url(front),
        "back_url": source_url(back),
    }


COINS = [
    coin(
        "10哥斯达黎加科朗",
        10,
        "/billetes-y-monedas/ImgMonedas/10-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/10-colones-reverso.png",
    ),
    coin(
        "25哥斯达黎加科朗（利蒙版）",
        25,
        "/billetes-y-monedas/ImgMonedas/25-anverso-corriente.png",
        "/billetes-y-monedas/ImgMonedas/25-reverso-corriente-limon.jpg",
    ),
    coin(
        "25哥斯达黎加科朗（蓬塔雷纳斯版）",
        25,
        "/billetes-y-monedas/ImgMonedas/25-anverso-corriente.png",
        "/billetes-y-monedas/ImgMonedas/25-reverso-corriente-puntarenas.jpg",
    ),
    coin(
        "25哥斯达黎加科朗（瓜纳卡斯特版）",
        25,
        "/billetes-y-monedas/ImgMonedas/25-anverso-corriente.png",
        "/billetes-y-monedas/ImgMonedas/25-reverso-corriente-guanacaste.jpg",
    ),
    coin(
        "25哥斯达黎加科朗（埃雷迪亚版）",
        25,
        "/billetes-y-monedas/ImgMonedas/25-anverso-corriente.png",
        "/billetes-y-monedas/ImgMonedas/25-reverso-corriente-heredia.jpg",
    ),
    coin(
        "25哥斯达黎加科朗（卡塔戈版）",
        25,
        "/billetes-y-monedas/ImgMonedas/25-anverso-corriente.png",
        "/billetes-y-monedas/ImgMonedas/25-reverso-corriente-cartago.jpg",
    ),
    coin(
        "25哥斯达黎加科朗（阿拉胡埃拉版）",
        25,
        "/billetes-y-monedas/ImgMonedas/25-anverso-corriente.png",
        "/billetes-y-monedas/ImgMonedas/25-reverso-corriente-alajuela.jpg",
    ),
    coin(
        "25哥斯达黎加科朗（圣何塞版）",
        25,
        "/billetes-y-monedas/ImgMonedas/25-anverso-corriente.png",
        "/billetes-y-monedas/ImgMonedas/25-reverso-corriente-san-jose.jpg",
    ),
    coin(
        "50哥斯达黎加科朗（云雾森林版）",
        50,
        "/billetes-y-monedas/ImgMonedas/50-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/50-colones-bosque-tropical-nuboso-corriente.png",
    ),
    coin(
        "50哥斯达黎加科朗（雨林版）",
        50,
        "/billetes-y-monedas/ImgMonedas/50-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/50-colones-bosque-tropical-lluvioso-corriente.png",
    ),
    coin(
        "50哥斯达黎加科朗（珊瑚礁版）",
        50,
        "/billetes-y-monedas/ImgMonedas/50-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/50-colones-arrecife-coralino-corriente.png",
    ),
    coin(
        "50哥斯达黎加科朗（干旱森林版）",
        50,
        "/billetes-y-monedas/ImgMonedas/50-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/50-colones-bosque-tropical-seco-corriente.png",
    ),
    coin(
        "50哥斯达黎加科朗（红树林版）",
        50,
        "/billetes-y-monedas/ImgMonedas/50-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/50-colones-manglar-corriente.png",
    ),
    coin(
        "50哥斯达黎加科朗（帕拉莫版）",
        50,
        "/billetes-y-monedas/ImgMonedas/50-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/50-colones-paramo-corriente.png",
    ),
    coin(
        "100哥斯达黎加科朗（秋千版）",
        100,
        "/billetes-y-monedas/ImgMonedas/100-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/100-colones-reverso-swing-corriente.png",
    ),
    coin(
        "500哥斯达黎加科朗（普通版）",
        500,
        "/billetes-y-monedas/ImgMonedas/500-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/500-colones-reverso-comun-corriente.png",
    ),
    coin(
        "500哥斯达黎加科朗（独立二百周年版）",
        500,
        "/billetes-y-monedas/ImgMonedas/500-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/500-colones-reverso-200-independencia-corriente.png",
    ),
    coin(
        "500哥斯达黎加科朗（共和国建立版）",
        500,
        "/billetes-y-monedas/ImgMonedas/500-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/500-colones-reverso-fundacion-republica-corriente.png",
    ),
    coin(
        "500哥斯达黎加科朗（废除军队版）",
        500,
        "/billetes-y-monedas/ImgMonedas/500-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/500-colones-reverso-abolicion-corriente.png",
    ),
    coin(
        "500哥斯达黎加科朗（瓜纳卡斯特并入版）",
        500,
        "/billetes-y-monedas/ImgMonedas/500-colones-anverso.png",
        "/billetes-y-monedas/ImgMonedas/500-colones-reverso-anexion-corriente.png",
    ),
]


def main() -> None:
    banknotes = [make_item(item, "banknote") for item in BANKNOTES]
    coins = [make_item(item, "coin") for item in COINS]

    data_path = ROOT / "currencies.json"
    data = json.loads(data_path.read_text())
    country = {
        "country": "哥斯达黎加",
        "country_en": "Costa Rica",
        "name": "哥斯达黎加科朗",
        "name_en": "Costa Rican colon",
        "symbol": "₡",
        "code": "CRC",
        "source_policy": (
            "Banco Central de Costa Rica current banknote and coin pages were used. "
            "The official coin page lists multiple current circulating reverse designs "
            "for 25, 50, and 500 colones; each listed corriente design is included as "
            "a separate denomination/design entry."
        ),
        "coin": coins,
        "banknote": banknotes,
    }
    index = next((i for i, item in enumerate(data) if item.get("country_en") == "Costa Rica"), None)
    if index is None:
        data.append(country)
    else:
        data[index] = country
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    log_path = ROOT / "collection_log.json"
    log = json.loads(log_path.read_text())
    log["costa_rica"] = {
        "status": "complete",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "coins": len(coins),
        "banknotes": len(banknotes),
        "sources": [BANKNOTES_SOURCE, COINS_SOURCE],
        "note": (
            "Current Costa Rican polymer banknotes and BCCR-listed corriente coin "
            "designs were downloaded from Banco Central de Costa Rica pages."
        ),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
