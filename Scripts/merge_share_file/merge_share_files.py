#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from pathlib import Path

from openpyxl import Workbook


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    csv_files = sorted(base_dir.glob("*_share.csv"))

    if not csv_files:
        raise SystemExit("未找到 *_share.csv 文件")

    rows = []
    for csv_file in csv_files:
        # 使用 utf-8-sig 以处理可能存在的 BOM
        with csv_file.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("文件名") or "").strip()
                link = (row.get("链接") or "").strip()
                if not name and not link:
                    continue
                rows.append((name, link))

    wb = Workbook()
    ws = wb.active
    ws.title = "merged"
    ws.append(["游戏资源名称", "游戏下载链接"])
    for name, link in rows:
        ws.append([name, link])

    output_path = base_dir / "merged_share.xlsx"
    wb.save(output_path)
    print(f"已生成: {output_path}")


if __name__ == "__main__":
    main()
