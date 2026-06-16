from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from app.services.csv_parser import (
    CSVValidationError,
    parse_campaigns_csv,
    parse_inventory_csv,
    parse_orders_csv,
    parse_returns_csv,
)


class CsvParserTest(unittest.TestCase):
    def _write_csv(self, content: str) -> Path:
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        handle.write(content)
        handle.close()
        return Path(handle.name)

    def test_returns_parser_accepts_alias_headers(self) -> None:
        csv_path = self._write_csv(
            "Refund Date,Parent SKU,Variant Name,Refund Total,Return Quantity,Reason\n"
            "2026-04-03,SKU-001,Black XL,699,2,Size mismatch\n"
        )

        rows = parse_returns_csv(csv_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].variant, "Black XL")
        self.assertEqual(rows[0].returned_units, 2)

    def test_returns_parser_falls_back_to_variant_sku_when_name_missing(self) -> None:
        csv_path = self._write_csv(
            "return-request-date,seller-sku,child-sku,refund-total,return-quantity,return-reason\n"
            "2026-04-03T10:15:00Z,SKU-001,SKU-001-BLK-XL,699,1,Too large\n"
        )

        rows = parse_returns_csv(csv_path)

        self.assertEqual(rows[0].variant, "SKU-001-BLK-XL")
        self.assertEqual(rows[0].variant_sku, "SKU-001-BLK-XL")

    def test_campaign_parser_derives_metrics_when_missing(self) -> None:
        csv_path = self._write_csv(
            "date,campaign id,advertised sku,cost,ad sales,clicks,conversions\n"
            "2026-04-01,CAMP-001,SKU-001,800,2000,40,4\n"
        )

        rows = parse_campaigns_csv(csv_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].acos, Decimal("40"))
        self.assertEqual(rows[0].roas, Decimal("2.5"))
        self.assertEqual(rows[0].conversion_rate, Decimal("10"))

    def test_orders_parser_accepts_hyphenated_headers_and_timestamps(self) -> None:
        csv_path = self._write_csv(
            "purchase-date,amazon-order-id,seller-sku,quantity-purchased,item-price,amazon-fees,refund-amount\n"
            "2026-04-01T08:00:00Z,ORDER-1,SKU-001,2,2000,300,0\n"
        )

        rows = parse_orders_csv(csv_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].order_id, "ORDER-1")
        self.assertEqual(rows[0].units, 2)

    def test_inventory_parser_sums_split_inbound_columns(self) -> None:
        csv_path = self._write_csv(
            "report-date,seller-sku,fulfillable-quantity,reserved-quantity,inbound-working-quantity,inbound-shipped-quantity,inbound-receiving-quantity,estimated-storage-fee-next-month\n"
            "2026/04/20,SKU-001,140,12,10,20,30,420\n"
        )

        rows = parse_inventory_csv(csv_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].inbound_units, 60)
        self.assertEqual(rows[0].monthly_storage_fee, Decimal("420"))

    def test_inventory_parser_rejects_wrong_dataset(self) -> None:
        csv_path = self._write_csv(
            "order_date,order_id,sku,units,revenue,fees,refund\n"
            "2026-04-01,ORD-1,SKU-001,1,1000,150,0\n"
        )

        with self.assertRaisesRegex(CSVValidationError, "looks like a orders CSV"):
            parse_inventory_csv(csv_path)


if __name__ == "__main__":
    unittest.main()
