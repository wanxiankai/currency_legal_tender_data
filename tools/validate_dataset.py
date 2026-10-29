#!/usr/bin/env python3
"""Validate the local legal-tender currency image dataset."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image


REQUIRED_TOP_LEVEL_FIELDS = {
    "country",
    "country_en",
    "name",
    "name_en",
    "symbol",
    "code",
    "coin",
    "banknote",
}

REQUIRED_ITEM_FIELDS = {
    "name",
    "value",
    "front_view_image",
    "back_view_image",
    "source",
    "years",
    "source_images",
    "original_front_image",
    "original_back_image",
    "original_source_images",
    "image_quality",
}


def image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    index_path = root / "currencies.json"

    try:
        records = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - reporting validation details
        return [f"currencies.json is not valid JSON: {exc}"]

    if not isinstance(records, list):
        return ["currencies.json must contain a top-level list"]

    seen_codes: set[str] = set()
    for country_index, country in enumerate(records):
        prefix = f"country[{country_index}]"
        if not isinstance(country, dict):
            errors.append(f"{prefix} must be an object")
            continue

        missing_top = REQUIRED_TOP_LEVEL_FIELDS - set(country)
        if missing_top:
            errors.append(f"{prefix} missing fields: {sorted(missing_top)}")

        code = country.get("code")
        if code in seen_codes:
            errors.append(f"{prefix} duplicate currency code: {code}")
        if isinstance(code, str):
            seen_codes.add(code)

        for kind in ("coin", "banknote"):
            items = country.get(kind, [])
            if not isinstance(items, list):
                errors.append(f"{prefix}.{kind} must be a list")
                continue

            for item_index, item in enumerate(items):
                item_prefix = f"{prefix}.{kind}[{item_index}]"
                if not isinstance(item, dict):
                    errors.append(f"{item_prefix} must be an object")
                    continue

                missing_item = REQUIRED_ITEM_FIELDS - set(item)
                if missing_item:
                    errors.append(
                        f"{item_prefix} missing fields: {sorted(missing_item)}"
                    )

                front = root / str(item.get("front_view_image", ""))
                back = root / str(item.get("back_view_image", ""))
                original_front = root / str(item.get("original_front_image", ""))
                original_back = root / str(item.get("original_back_image", ""))

                for label, path in (
                    ("front", front),
                    ("back", back),
                    ("original_front", original_front),
                    ("original_back", original_back),
                ):
                    if not path.is_file():
                        errors.append(f"{item_prefix} missing {label} image: {path}")

                if front.is_file() and back.is_file():
                    front_size = image_size(front)
                    back_size = image_size(back)
                    if front_size != back_size:
                        errors.append(
                            f"{item_prefix} front/back size mismatch: "
                            f"{front_size} != {back_size}"
                        )

                    quality = item.get("image_quality", {})
                    if isinstance(quality, dict):
                        if quality.get("normalized_same_size") is not True:
                            errors.append(
                                f"{item_prefix} image_quality.normalized_same_size "
                                "must be true"
                            )
                        if quality.get("final_width") != front_size[0]:
                            errors.append(
                                f"{item_prefix} final_width "
                                f"{quality.get('final_width')} != {front_size[0]}"
                            )
                        if quality.get("final_height") != front_size[1]:
                            errors.append(
                                f"{item_prefix} final_height "
                                f"{quality.get('final_height')} != {front_size[1]}"
                            )
                    else:
                        errors.append(f"{item_prefix} image_quality must be an object")

                if original_front.is_file() and original_back.is_file():
                    front_original_size = image_size(original_front)
                    back_original_size = image_size(original_back)
                    quality = item.get("image_quality", {})
                    if isinstance(quality, dict):
                        expected = {
                            "front_original_width": front_original_size[0],
                            "front_original_height": front_original_size[1],
                            "back_original_width": back_original_size[0],
                            "back_original_height": back_original_size[1],
                        }
                        for key, value in expected.items():
                            if quality.get(key) != value:
                                errors.append(
                                    f"{item_prefix} {key} "
                                    f"{quality.get(key)} != {value}"
                                )

    return errors


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    errors = validate(root)
    if errors:
        print(f"Validation failed with {len(errors)} issue(s):")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
