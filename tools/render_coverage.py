#!/usr/bin/env python3
"""Render docs/COVERAGE.md from the canonical currencies.json index."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def country_directory(country: dict) -> str:
    """Return the actual top-level directory used by an indexed record."""
    for kind in ("coin", "banknote"):
        for item in country.get(kind, []):
            image_path = Path(str(item.get("front_view_image", "")))
            if len(image_path.parts) > 1:
                return image_path.parts[0]
    return str(country["country_en"]).replace(" ", "_")


def render(records: list[dict], as_of: str) -> str:
    coin_count = sum(len(country["coin"]) for country in records)
    banknote_count = sum(len(country["banknote"]) for country in records)
    both_count = sum(
        bool(country["coin"]) and bool(country["banknote"])
        for country in records
    )
    banknote_only_count = sum(
        not country["coin"] and bool(country["banknote"])
        for country in records
    )
    coin_only_count = sum(
        bool(country["coin"]) and not country["banknote"]
        for country in records
    )

    lines = [
        "# 收录明细",
        "",
        "> 本文档由 `tools/render_coverage.py` 根据 `currencies.json` 生成，请勿手工维护统计和目录。",
        "> 统计口径：按 `currencies.json` 中的“面额/版别”条目计数；"
        "同一面额的不同现行设计会分别计数。",
        f"> 数据核对日期：{as_of}。`currencies.json` 始终是路径、字段和来源信息的唯一权威来源。",
        "",
        "## 总览",
        "",
        "| 指标 | 数量 |",
        "| --- | ---: |",
        f"| 国家/发行地区 | {len(records)} |",
        f"| 硬币条目 | {coin_count} |",
        f"| 纸币条目 | {banknote_count} |",
        f"| 合计 | {coin_count + banknote_count} |",
        f"| 同时覆盖硬币与纸币 | {both_count} |",
        f"| 仅覆盖纸币 | {banknote_only_count} |",
        f"| 仅覆盖硬币 | {coin_only_count} |",
        "",
        "## 分国家/地区明细",
        "",
    ]

    for country in records:
        lines.extend(
            [
                f"## {country['country']} / {country['country_en']} · {country['code']}",
                "",
                f"- 数据目录：`{country_directory(country)}/`",
                (
                    f"- 货币：{country['name']} / {country['name_en']}"
                    f"（{country['symbol']}）"
                ),
            ]
        )
        for kind, label in (("coin", "硬币"), ("banknote", "纸币")):
            items = country[kind]
            names = "、".join(item["name"] for item in items) if items else "未收录"
            lines.append(f"- {label}（{len(items)}）：{names}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--as-of",
        default=date.today().isoformat(),
        help="Date shown in the document header (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "COVERAGE.md",
        help="Output path.",
    )
    args = parser.parse_args()

    records = json.loads((ROOT / "currencies.json").read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise SystemExit("currencies.json must contain a top-level list")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(records, args.as_of), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
