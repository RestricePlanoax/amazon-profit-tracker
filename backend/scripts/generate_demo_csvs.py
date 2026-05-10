from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
ORDERS_PATH = ROOT_DIR / "sample_orders.csv"
ADS_PATH = ROOT_DIR / "sample_ads.csv"


def daterange(start: date, end: date, step_days: int) -> list[date]:
    values: list[date] = []
    cursor = start
    while cursor <= end:
        values.append(cursor)
        cursor += timedelta(days=step_days)
    return values


def build_orders_rows() -> list[list[str | int]]:
    skus = [
        ("SKU-001", 999),
        ("SKU-002", 1499),
        ("SKU-003", 799),
        ("SKU-004", 1899),
    ]
    rows: list[list[str | int]] = []
    order_counter = 1

    for index, order_date in enumerate(daterange(date(2024, 1, 1), date(2026, 4, 21), 7)):
        seasonal_boost = 1 + ((index % 9) * 0.04)
        for sku_index, (sku, base_price) in enumerate(skus):
            units = 1 + ((index + sku_index) % 4)
            revenue = int(base_price * units * seasonal_boost)
            fees = int(revenue * (0.14 + sku_index * 0.01))
            refund = 0

            if (index + sku_index) % 11 == 0:
                refund = int(revenue * 0.08)
            elif (index + sku_index) % 17 == 0:
                refund = int(revenue * 0.04)

            rows.append(
                [
                    order_date.isoformat(),
                    f"ORD{order_counter:04d}",
                    sku,
                    units,
                    revenue,
                    fees,
                    refund,
                ]
            )
            order_counter += 1

    return rows


def build_ads_rows() -> list[list[str | int]]:
    skus = [
        ("SKU-001", 1.0),
        ("SKU-002", 0.92),
        ("SKU-003", 0.88),
        ("SKU-004", 1.08),
    ]
    rows: list[list[str | int]] = []

    for index, metric_date in enumerate(daterange(date(2024, 1, 1), date(2026, 4, 21), 7)):
        for sku_index, (sku, multiplier) in enumerate(skus):
            base_impressions = 1800 + ((index + 2 * sku_index) % 12) * 140
            clicks = 28 + ((index * (sku_index + 2)) % 18)
            spend = int((220 + sku_index * 35 + (index % 8) * 18) * multiplier)
            sales = int(spend * (4.1 - sku_index * 0.35 + ((index % 5) * 0.08)))

            rows.append(
                [
                    metric_date.isoformat(),
                    sku,
                    spend,
                    sales,
                    clicks,
                    base_impressions,
                ]
            )

    return rows


def write_csv(path: Path, headers: list[str], rows: list[list[str | int]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def main() -> None:
    write_csv(
        ORDERS_PATH,
        ["order_date", "order_id", "sku", "units", "revenue", "fees", "refund"],
        build_orders_rows(),
    )
    write_csv(
        ADS_PATH,
        ["date", "sku", "spend", "sales", "clicks", "impressions"],
        build_ads_rows(),
    )


if __name__ == "__main__":
    main()
