from __future__ import annotations

import unittest
from decimal import Decimal

from app.services.profit_analysis_service import (
    SkuPeriodSnapshot,
    detect_ad_spend_waste,
    detect_fee_change,
    detect_margin_drop,
    detect_return_spike,
)


def build_snapshot(**overrides) -> SkuPeriodSnapshot:
    payload = {
        "sku": "SKU-001",
        "name": "Test Product",
        "current_revenue": Decimal("12000"),
        "previous_revenue": Decimal("12000"),
        "current_ad_spend": Decimal("4200"),
        "previous_ad_spend": Decimal("2500"),
        "current_fees": Decimal("2500"),
        "previous_fees": Decimal("1500"),
        "current_refund": Decimal("1200"),
        "previous_refund": Decimal("120"),
        "current_units_sold": 20,
        "previous_units_sold": 20,
        "current_net_profit": Decimal("1200"),
        "previous_net_profit": Decimal("4200"),
        "current_profit_margin": Decimal("10"),
        "previous_profit_margin": Decimal("35"),
        "current_return_rate": Decimal("10"),
        "previous_return_rate": Decimal("1"),
        "current_acos": Decimal("48"),
        "previous_acos": Decimal("22"),
    }
    payload.update(overrides)
    return SkuPeriodSnapshot(**payload)


class ProfitAnalysisRulesTest(unittest.TestCase):
    def test_detect_margin_drop_creates_alert(self) -> None:
        alert = detect_margin_drop(build_snapshot())
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, "margin_drop")

    def test_detect_ad_spend_waste_requires_flat_sales(self) -> None:
        alert = detect_ad_spend_waste(
            build_snapshot(current_revenue=Decimal("12300"), previous_revenue=Decimal("12000"))
        )
        self.assertIsNotNone(alert)

        no_alert = detect_ad_spend_waste(
            build_snapshot(current_revenue=Decimal("18000"), previous_revenue=Decimal("12000"))
        )
        self.assertIsNone(no_alert)

    def test_detect_return_spike_uses_rate_jump(self) -> None:
        alert = detect_return_spike(build_snapshot())
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, "return_spike")

        no_alert = detect_return_spike(
            build_snapshot(current_return_rate=Decimal("3"), previous_return_rate=Decimal("1"))
        )
        self.assertIsNone(no_alert)

    def test_detect_fee_change_requires_meaningful_increase(self) -> None:
        alert = detect_fee_change(build_snapshot())
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, "unexpected_fee")

        no_alert = detect_fee_change(
            build_snapshot(
                current_fees=Decimal("1600"),
                previous_fees=Decimal("1500"),
                current_revenue=Decimal("12000"),
                previous_revenue=Decimal("12000"),
            )
        )
        self.assertIsNone(no_alert)


if __name__ == "__main__":
    unittest.main()
