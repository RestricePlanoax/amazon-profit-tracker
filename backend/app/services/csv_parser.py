from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


class CSVValidationError(ValueError):
    pass


ORDERS_REQUIRED_COLUMNS = {
    "order_date",
    "sku",
    "units",
    "revenue",
}

ADS_REQUIRED_COLUMNS = {"date", "sku", "spend"}
SETTLEMENT_REQUIRED_COLUMNS = {
    "settlement_date",
    "total_amount",
}
RETURNS_REQUIRED_COLUMNS = {
    "return_date",
    "sku",
}
REIMBURSEMENTS_REQUIRED_COLUMNS = {
    "detected_at",
    "sku",
    "issue_type",
    "amount",
}
CAMPAIGN_REQUIRED_COLUMNS = {
    "metric_date",
    "campaign_id",
    "sku",
    "spend",
    "clicks",
    "orders",
}
INVENTORY_REQUIRED_COLUMNS = {
    "snapshot_date",
    "sku",
    "available_units",
}

ORDERS_SIGNATURE_COLUMNS = {"order_date", "order_id", "units", "revenue", "fees", "refund"}
ADS_SIGNATURE_COLUMNS = {"date", "spend", "sales", "clicks", "impressions"}
SETTLEMENT_SIGNATURE_COLUMNS = {
    "settlement_date",
    "settlement_id",
    "total_amount",
    "taxes",
    "reimbursements",
}
RETURNS_SIGNATURE_COLUMNS = {
    "return_date",
    "variant",
    "variant_sku",
    "return_reason",
    "refund_amount",
    "returned_units",
}
REIMBURSEMENTS_SIGNATURE_COLUMNS = {
    "detected_at",
    "issue_type",
    "amount",
    "claim_deadline",
    "claimed",
    "received",
}
CAMPAIGN_SIGNATURE_COLUMNS = {
    "metric_date",
    "campaign_id",
    "sales",
    "clicks",
    "orders",
    "acos",
    "roas",
}
INVENTORY_SIGNATURE_COLUMNS = {
    "snapshot_date",
    "available_units",
    "reserved_units",
    "inbound_units",
    "inbound_working_units",
    "inbound_shipped_units",
    "inbound_receiving_units",
    "days_in_storage",
    "monthly_storage_fee",
}

ORDERS_COLUMN_ALIASES = {
    "order_date": {
        "order_date",
        "purchase_date",
        "orderdate",
        "date",
        "purchase-date",
        "purchase_date_pst",
        "purchase_date_utc",
    },
    "order_id": {"order_id", "amazon_order_id", "amazonorderid", "amazon-order-id"},
    "sku": {"sku", "seller_sku", "merchant_sku", "seller-sku", "merchant-sku"},
    "units": {
        "units",
        "quantity",
        "quantity_ordered",
        "units_ordered",
        "quantity_purchased",
        "quantity-purchased",
    },
    "revenue": {
        "revenue",
        "sales",
        "item_price",
        "principal",
        "sales_amount",
        "product_sales",
        "item-price",
        "product-sales",
    },
    "fees": {
        "fees",
        "fee",
        "commission",
        "commission_amount",
        "amazon_fees",
        "amazon-fees",
        "selling_fees",
        "selling-fees",
    },
    "refund": {"refund", "refund_amount", "refunds", "refund-amount", "total_refund"},
}

ADS_COLUMN_ALIASES = {
    "date": {"date", "day", "report_date", "report-date"},
    "sku": {"sku", "seller_sku", "advertised_sku", "advertised-sku", "seller-sku"},
    "spend": {"spend", "cost", "ad_spend", "ad-spend"},
    "sales": {
        "sales",
        "ad_sales",
        "attributed_sales_7d",
        "seven_day_total_sales",
        "7_day_total_sales",
        "7daytotalsales",
        "attributed_sales_14d",
        "14_day_total_sales",
    },
    "clicks": {"clicks", "click_throughs", "click-throughs"},
    "impressions": {"impressions", "ad_impressions", "ad-impressions"},
}

SETTLEMENT_COLUMN_ALIASES = {
    "settlement_date": {
        "settlement_date",
        "posted_date",
        "date",
        "settlement_start_date",
        "settlement-start-date",
        "deposit_date",
        "deposit-date",
    },
    "settlement_id": {"settlement_id", "settlementid", "id", "settlement-id"},
    "total_amount": {"total_amount", "amount", "total", "total_amount_usd", "total-amount"},
    "fees": {"fees", "total_fees", "amazon_fees", "amazon-fees", "other_transaction_fees"},
    "taxes": {"taxes", "tax_amount", "tax", "tax-amount"},
    "reimbursements": {
        "reimbursements",
        "reimbursement",
        "reimbursement_amount",
        "reimbursement-amount",
    },
}
RETURNS_COLUMN_ALIASES = {
    "return_date": {
        "return_date",
        "date",
        "refund_date",
        "returnrequestdate",
        "return_request_date",
        "return-request-date",
    },
    "sku": {"sku", "seller_sku", "merchant_sku", "parent_sku", "seller-sku"},
    "variant": {"variant", "variant_name", "variant-name", "size_color", "option_name"},
    "variant_sku": {"variant_sku", "child_sku", "childsku", "seller_variant_sku", "child-sku"},
    "return_reason": {"return_reason", "reason", "returnreason", "refund_reason", "return-reason"},
    "refund_amount": {"refund_amount", "refund", "refunds", "refundtotal", "refund-total"},
    "returned_units": {"returned_units", "units_returned", "quantity", "return_quantity", "return-quantity"},
}
REIMBURSEMENTS_COLUMN_ALIASES = {
    "detected_at": {"detected_at", "date", "issue_date", "reported_date", "reported-date"},
    "sku": {"sku", "seller_sku", "merchant_sku", "seller-sku"},
    "issue_type": {
        "issue_type",
        "reason",
        "event_type",
        "adjustment_type",
        "reimbursement_type",
        "disposition",
    },
    "amount": {"amount", "reimbursement_amount", "value", "reimbursement-amount"},
    "status": {"status", "case_status", "case-status"},
    "claim_deadline": {"claim_deadline", "deadline", "expiry_date", "expiration_date"},
    "claimed": {"claimed", "is_claimed", "claim_submitted"},
    "received": {"received", "is_received", "payment_received"},
}
CAMPAIGN_COLUMN_ALIASES = {
    "metric_date": {"metric_date", "date", "day"},
    "campaign_id": {"campaign_id", "campaignid", "campaign-id"},
    "campaign_name": {"campaign_name", "campaign", "campaign-name"},
    "sku": {"sku", "advertised_sku", "advertised-sku", "seller_sku"},
    "spend": {"spend", "cost", "ad_spend"},
    "sales": {
        "sales",
        "ad_sales",
        "attributed_sales_7d",
        "seven_day_total_sales",
        "7_day_total_sales",
        "7daytotalsales",
        "attributed_sales_14d",
        "14_day_total_sales",
    },
    "clicks": {"clicks", "click_throughs", "click-throughs"},
    "orders": {
        "orders",
        "conversions",
        "attributed_conversions_7d",
        "7_day_total_orders",
        "7daytotalorders",
        "7_day_total_orders_",
        "14_day_total_orders",
    },
    "acos": {"acos"},
    "roas": {"roas"},
    "conversion_rate": {"conversion_rate", "cvr", "conversion-rate"},
}
INVENTORY_COLUMN_ALIASES = {
    "snapshot_date": {"snapshot_date", "date", "report_date", "report-date"},
    "sku": {"sku", "seller_sku", "merchant_sku", "seller-sku"},
    "available_units": {
        "available_units",
        "available",
        "fulfillable_quantity",
        "afn_fulfillable_quantity",
        "fulfillable-quantity",
    },
    "reserved_units": {"reserved_units", "reserved", "total_reserved_quantity", "reserved-quantity"},
    "inbound_units": {"inbound_units", "inbound", "afn_inbound_quantity"},
    "inbound_working_units": {"inbound_working_units", "inbound_working_quantity"},
    "inbound_shipped_units": {"inbound_shipped_units", "inbound_shipped_quantity"},
    "inbound_receiving_units": {"inbound_receiving_units", "inbound_receiving_quantity"},
    "days_in_storage": {
        "days_in_storage",
        "inventory_age_days",
        "aging_days",
        "age",
        "storage_age_days",
    },
    "monthly_storage_fee": {
        "monthly_storage_fee",
        "storage_fee",
        "estimated_storage_fee",
        "estimated_storage_fee_next_month",
    },
}


@dataclass(slots=True)
class ParsedOrderRow:
    order_date: date
    order_id: str | None
    sku: str
    units: int
    revenue: Decimal
    fees: Decimal
    refund: Decimal


@dataclass(slots=True)
class ParsedAdRow:
    date: date
    sku: str
    spend: Decimal
    sales: Decimal
    clicks: int
    impressions: int


@dataclass(slots=True)
class ParsedSettlementRow:
    settlement_date: date
    settlement_id: str | None
    total_amount: Decimal
    fees: Decimal
    taxes: Decimal
    reimbursements: Decimal


@dataclass(slots=True)
class ParsedReturnRow:
    return_date: date
    sku: str
    variant: str
    variant_sku: str | None
    return_reason: str | None
    refund_amount: Decimal
    returned_units: int


@dataclass(slots=True)
class ParsedReimbursementRow:
    detected_at: date
    sku: str
    issue_type: str
    amount: Decimal
    status: str
    claim_deadline: date | None
    claimed: bool
    received: bool


@dataclass(slots=True)
class ParsedCampaignRow:
    metric_date: date
    campaign_id: str
    campaign_name: str | None
    sku: str
    spend: Decimal
    sales: Decimal
    clicks: int
    orders: int
    acos: Decimal
    roas: Decimal
    conversion_rate: Decimal


@dataclass(slots=True)
class ParsedInventoryRow:
    snapshot_date: date
    sku: str
    available_units: int
    reserved_units: int
    inbound_units: int
    days_in_storage: int | None
    monthly_storage_fee: Decimal | None


def normalize_column_name(name: str) -> str:
    normalized = name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_")


def _canonicalize_header(name: str, aliases: dict[str, set[str]] | None) -> str:
    normalized = normalize_column_name(name)
    compact = normalized.replace("_", "")

    if not aliases:
        return normalized

    for canonical, options in aliases.items():
        if normalized in options or compact in options:
            return canonical

    return normalized


def _prepare_reader(
    handle,
    aliases: dict[str, set[str]] | None = None,
) -> csv.DictReader[str]:
    sample = handle.read(4096)
    handle.seek(0)

    if not sample.strip():
        raise CSVValidationError("CSV file is empty.")

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        if not any(delimiter in sample for delimiter in [",", ";", "\t", "|"]):
            raise CSVValidationError("Unsupported delimiter or empty file.")
        dialect = csv.excel

    reader = csv.DictReader(handle, dialect=dialect)
    if not reader.fieldnames:
        raise CSVValidationError("CSV file is missing a header row.")
    reader.fieldnames = [
        _canonicalize_header(field or "", aliases) for field in reader.fieldnames
    ]
    return reader


def _ensure_required_columns(
    reader: csv.DictReader[str],
    required_columns: set[str],
    *,
    upload_type: str,
    alternate_datasets: dict[str, set[str]] | None = None,
) -> None:
    available = set(reader.fieldnames or [])
    missing = sorted(required_columns - available)
    if missing:
        if alternate_datasets:
            for alternate_type, alternate_columns in alternate_datasets.items():
                overlap = len(available & alternate_columns)
                threshold = max(2, min(len(alternate_columns), 3))
                if alternate_columns.issubset(available) or overlap >= threshold:
                    raise CSVValidationError(
                        f"This looks like a {alternate_type} CSV uploaded to the {upload_type} endpoint. "
                        f"Please upload it in the {alternate_type} box instead."
                    )
        raise CSVValidationError(
            f"CSV is missing required columns: {', '.join(missing)}."
        )


def _parse_date(raw_value: str, row_number: int, column_name: str) -> date:
    value = raw_value.strip()
    if not value:
        raise CSVValidationError(f"Row {row_number}: '{column_name}' is required.")
    normalized_value = value.replace("/", "-")
    candidates = [
        normalized_value,
        normalized_value[:10] if len(normalized_value) >= 10 else normalized_value,
    ]

    for candidate in candidates:
        try:
            return date.fromisoformat(candidate)
        except ValueError:
            pass

    iso_candidate = normalized_value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_candidate).date()
    except ValueError:
        pass

    for pattern in ("%m-%d-%Y", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue

    raise CSVValidationError(
        f"Row {row_number}: '{column_name}' must be a recognizable date like YYYY-MM-DD."
    )


def _parse_int(
    raw_value: str | None,
    row_number: int,
    column_name: str,
    *,
    default: int | None = None,
) -> int:
    value = (raw_value or "").strip()
    if not value:
        if default is not None:
            return default
        raise CSVValidationError(f"Row {row_number}: '{column_name}' is required.")
    try:
        return int(value)
    except ValueError as exc:
        raise CSVValidationError(
            f"Row {row_number}: '{column_name}' must be an integer."
        ) from exc


def _parse_decimal(
    raw_value: str | None,
    row_number: int,
    column_name: str,
    *,
    default: Decimal | None = None,
) -> Decimal:
    value = (raw_value or "").strip()
    if not value:
        if default is not None:
            return default
        raise CSVValidationError(f"Row {row_number}: '{column_name}' is required.")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise CSVValidationError(
            f"Row {row_number}: '{column_name}' must be a valid number."
        ) from exc


def _parse_sku(raw_value: str | None, row_number: int) -> str:
    value = (raw_value or "").strip()
    if not value:
        raise CSVValidationError(f"Row {row_number}: 'sku' is required.")
    return value


def _parse_optional_date(raw_value: str | None, row_number: int, column_name: str) -> date | None:
    value = (raw_value or "").strip()
    if not value:
        return None
    return _parse_date(value, row_number, column_name)


def _parse_bool(raw_value: str | None, row_number: int, column_name: str, *, default: bool = False) -> bool:
    value = (raw_value or "").strip().lower()
    if not value:
        return default
    if value in {"true", "yes", "1", "y"}:
        return True
    if value in {"false", "no", "0", "n"}:
        return False
    raise CSVValidationError(
        f"Row {row_number}: '{column_name}' must be true/false, yes/no, or 1/0."
    )


def parse_orders_csv(file_path: str | Path) -> list[ParsedOrderRow]:
    rows: list[ParsedOrderRow] = []
    with Path(file_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = _prepare_reader(handle, ORDERS_COLUMN_ALIASES)
        _ensure_required_columns(
            reader,
            ORDERS_REQUIRED_COLUMNS,
            upload_type="orders",
            alternate_datasets={
                "ads": ADS_SIGNATURE_COLUMNS,
                "settlement": SETTLEMENT_SIGNATURE_COLUMNS,
                "returns": RETURNS_SIGNATURE_COLUMNS,
                "reimbursements": REIMBURSEMENTS_SIGNATURE_COLUMNS,
                "campaigns": CAMPAIGN_SIGNATURE_COLUMNS,
                "inventory": INVENTORY_SIGNATURE_COLUMNS,
            },
        )
        for row_number, row in enumerate(reader, start=2):
            rows.append(
                ParsedOrderRow(
                    order_date=_parse_date(row.get("order_date", ""), row_number, "order_date"),
                    order_id=(row.get("order_id") or "").strip() or None,
                    sku=_parse_sku(row.get("sku"), row_number),
                    units=_parse_int(row.get("units"), row_number, "units"),
                    revenue=_parse_decimal(row.get("revenue"), row_number, "revenue"),
                    fees=_parse_decimal(
                        row.get("fees"),
                        row_number,
                        "fees",
                        default=Decimal("0"),
                    ),
                    refund=_parse_decimal(
                        row.get("refund"),
                        row_number,
                        "refund",
                        default=Decimal("0"),
                    ),
                )
            )

    if not rows:
        raise CSVValidationError("Orders CSV has no data rows.")

    return rows


def parse_ads_csv(file_path: str | Path) -> list[ParsedAdRow]:
    rows: list[ParsedAdRow] = []
    with Path(file_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = _prepare_reader(handle, ADS_COLUMN_ALIASES)
        _ensure_required_columns(
            reader,
            ADS_REQUIRED_COLUMNS,
            upload_type="ads",
            alternate_datasets={
                "orders": ORDERS_SIGNATURE_COLUMNS,
                "settlement": SETTLEMENT_SIGNATURE_COLUMNS,
                "returns": RETURNS_SIGNATURE_COLUMNS,
                "reimbursements": REIMBURSEMENTS_SIGNATURE_COLUMNS,
                "campaigns": CAMPAIGN_SIGNATURE_COLUMNS,
                "inventory": INVENTORY_SIGNATURE_COLUMNS,
            },
        )
        for row_number, row in enumerate(reader, start=2):
            rows.append(
                ParsedAdRow(
                    date=_parse_date(row.get("date", ""), row_number, "date"),
                    sku=_parse_sku(row.get("sku"), row_number),
                    spend=_parse_decimal(
                        row.get("spend"),
                        row_number,
                        "spend",
                        default=Decimal("0"),
                    ),
                    sales=_parse_decimal(
                        row.get("sales"),
                        row_number,
                        "sales",
                        default=Decimal("0"),
                    ),
                    clicks=_parse_int(
                        row.get("clicks"),
                        row_number,
                        "clicks",
                        default=0,
                    ),
                    impressions=_parse_int(
                        row.get("impressions"),
                        row_number,
                        "impressions",
                        default=0,
                    ),
                )
            )

    if not rows:
        raise CSVValidationError("Ads CSV has no data rows.")

    return rows


def parse_settlement_csv(file_path: str | Path) -> list[ParsedSettlementRow]:
    rows: list[ParsedSettlementRow] = []
    with Path(file_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = _prepare_reader(handle, SETTLEMENT_COLUMN_ALIASES)
        _ensure_required_columns(
            reader,
            SETTLEMENT_REQUIRED_COLUMNS,
            upload_type="settlement",
            alternate_datasets={
                "orders": ORDERS_SIGNATURE_COLUMNS,
                "ads": ADS_SIGNATURE_COLUMNS,
                "returns": RETURNS_SIGNATURE_COLUMNS,
                "reimbursements": REIMBURSEMENTS_SIGNATURE_COLUMNS,
                "campaigns": CAMPAIGN_SIGNATURE_COLUMNS,
                "inventory": INVENTORY_SIGNATURE_COLUMNS,
            },
        )
        for row_number, row in enumerate(reader, start=2):
            rows.append(
                ParsedSettlementRow(
                    settlement_date=_parse_date(
                        row.get("settlement_date", ""),
                        row_number,
                        "settlement_date",
                    ),
                    settlement_id=(row.get("settlement_id") or "").strip() or None,
                    total_amount=_parse_decimal(
                        row.get("total_amount"),
                        row_number,
                        "total_amount",
                        default=Decimal("0"),
                    ),
                    fees=_parse_decimal(
                        row.get("fees"),
                        row_number,
                        "fees",
                        default=Decimal("0"),
                    ),
                    taxes=_parse_decimal(
                        row.get("taxes"),
                        row_number,
                        "taxes",
                        default=Decimal("0"),
                    ),
                    reimbursements=_parse_decimal(
                        row.get("reimbursements"),
                        row_number,
                        "reimbursements",
                        default=Decimal("0"),
                    ),
                )
            )

    if not rows:
        raise CSVValidationError("Settlement CSV has no data rows.")

    return rows


def parse_returns_csv(file_path: str | Path) -> list[ParsedReturnRow]:
    rows: list[ParsedReturnRow] = []
    with Path(file_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = _prepare_reader(handle, RETURNS_COLUMN_ALIASES)
        _ensure_required_columns(
            reader,
            RETURNS_REQUIRED_COLUMNS,
            upload_type="returns",
            alternate_datasets={
                "orders": ORDERS_SIGNATURE_COLUMNS,
                "ads": ADS_SIGNATURE_COLUMNS,
                "settlement": SETTLEMENT_SIGNATURE_COLUMNS,
                "reimbursements": REIMBURSEMENTS_SIGNATURE_COLUMNS,
                "campaigns": CAMPAIGN_SIGNATURE_COLUMNS,
                "inventory": INVENTORY_SIGNATURE_COLUMNS,
            },
        )
        for row_number, row in enumerate(reader, start=2):
            variant_sku = (row.get("variant_sku") or "").strip() or None
            variant = (row.get("variant") or "").strip() or variant_sku or _parse_sku(row.get("sku"), row_number)
            rows.append(
                ParsedReturnRow(
                    return_date=_parse_date(row.get("return_date", ""), row_number, "return_date"),
                    sku=_parse_sku(row.get("sku"), row_number),
                    variant=variant,
                    variant_sku=variant_sku,
                    return_reason=(row.get("return_reason") or "").strip() or None,
                    refund_amount=_parse_decimal(
                        row.get("refund_amount"),
                        row_number,
                        "refund_amount",
                        default=Decimal("0"),
                    ),
                    returned_units=_parse_int(
                        row.get("returned_units"),
                        row_number,
                        "returned_units",
                        default=1,
                    ),
                )
            )

    if not rows:
        raise CSVValidationError("Returns CSV has no data rows.")

    return rows


def parse_reimbursements_csv(file_path: str | Path) -> list[ParsedReimbursementRow]:
    rows: list[ParsedReimbursementRow] = []
    with Path(file_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = _prepare_reader(handle, REIMBURSEMENTS_COLUMN_ALIASES)
        _ensure_required_columns(
            reader,
            REIMBURSEMENTS_REQUIRED_COLUMNS,
            upload_type="reimbursements",
            alternate_datasets={
                "orders": ORDERS_SIGNATURE_COLUMNS,
                "ads": ADS_SIGNATURE_COLUMNS,
                "settlement": SETTLEMENT_SIGNATURE_COLUMNS,
                "returns": RETURNS_SIGNATURE_COLUMNS,
                "campaigns": CAMPAIGN_SIGNATURE_COLUMNS,
                "inventory": INVENTORY_SIGNATURE_COLUMNS,
            },
        )
        for row_number, row in enumerate(reader, start=2):
            issue_type = (row.get("issue_type") or "").strip()
            if not issue_type:
                raise CSVValidationError(f"Row {row_number}: 'issue_type' is required.")
            rows.append(
                ParsedReimbursementRow(
                    detected_at=_parse_date(row.get("detected_at", ""), row_number, "detected_at"),
                    sku=_parse_sku(row.get("sku"), row_number),
                    issue_type=issue_type,
                    amount=_parse_decimal(row.get("amount"), row_number, "amount"),
                    status=(row.get("status") or "pending").strip() or "pending",
                    claim_deadline=_parse_optional_date(
                        row.get("claim_deadline"), row_number, "claim_deadline"
                    ),
                    claimed=_parse_bool(row.get("claimed"), row_number, "claimed", default=False),
                    received=_parse_bool(row.get("received"), row_number, "received", default=False),
                )
            )

    if not rows:
        raise CSVValidationError("Reimbursements CSV has no data rows.")

    return rows


def parse_campaigns_csv(file_path: str | Path) -> list[ParsedCampaignRow]:
    rows: list[ParsedCampaignRow] = []
    with Path(file_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = _prepare_reader(handle, CAMPAIGN_COLUMN_ALIASES)
        _ensure_required_columns(
            reader,
            CAMPAIGN_REQUIRED_COLUMNS,
            upload_type="campaigns",
            alternate_datasets={
                "orders": ORDERS_SIGNATURE_COLUMNS,
                "ads": ADS_SIGNATURE_COLUMNS,
                "settlement": SETTLEMENT_SIGNATURE_COLUMNS,
                "returns": RETURNS_SIGNATURE_COLUMNS,
                "reimbursements": REIMBURSEMENTS_SIGNATURE_COLUMNS,
                "inventory": INVENTORY_SIGNATURE_COLUMNS,
            },
        )
        for row_number, row in enumerate(reader, start=2):
            campaign_id = (row.get("campaign_id") or "").strip()
            if not campaign_id:
                raise CSVValidationError(f"Row {row_number}: 'campaign_id' is required.")

            spend = _parse_decimal(row.get("spend"), row_number, "spend", default=Decimal("0"))
            sales = _parse_decimal(row.get("sales"), row_number, "sales", default=Decimal("0"))
            clicks = _parse_int(row.get("clicks"), row_number, "clicks", default=0)
            orders = _parse_int(row.get("orders"), row_number, "orders", default=0)
            acos = _parse_decimal(
                row.get("acos"),
                row_number,
                "acos",
                default=(spend / sales * Decimal("100")) if sales else Decimal("0"),
            )
            roas = _parse_decimal(
                row.get("roas"),
                row_number,
                "roas",
                default=(sales / spend) if spend else Decimal("0"),
            )
            conversion_rate = _parse_decimal(
                row.get("conversion_rate"),
                row_number,
                "conversion_rate",
                default=(Decimal(orders) / Decimal(clicks) * Decimal("100")) if clicks else Decimal("0"),
            )

            rows.append(
                ParsedCampaignRow(
                    metric_date=_parse_date(row.get("metric_date", ""), row_number, "metric_date"),
                    campaign_id=campaign_id,
                    campaign_name=(row.get("campaign_name") or "").strip() or None,
                    sku=_parse_sku(row.get("sku"), row_number),
                    spend=spend,
                    sales=sales,
                    clicks=clicks,
                    orders=orders,
                    acos=acos,
                    roas=roas,
                    conversion_rate=conversion_rate,
                )
            )

    if not rows:
        raise CSVValidationError("Campaign CSV has no data rows.")

    return rows


def parse_inventory_csv(file_path: str | Path) -> list[ParsedInventoryRow]:
    rows: list[ParsedInventoryRow] = []
    with Path(file_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = _prepare_reader(handle, INVENTORY_COLUMN_ALIASES)
        _ensure_required_columns(
            reader,
            INVENTORY_REQUIRED_COLUMNS,
            upload_type="inventory",
            alternate_datasets={
                "orders": ORDERS_SIGNATURE_COLUMNS,
                "ads": ADS_SIGNATURE_COLUMNS,
                "settlement": SETTLEMENT_SIGNATURE_COLUMNS,
                "returns": RETURNS_SIGNATURE_COLUMNS,
                "reimbursements": REIMBURSEMENTS_SIGNATURE_COLUMNS,
                "campaigns": CAMPAIGN_SIGNATURE_COLUMNS,
            },
        )
        for row_number, row in enumerate(reader, start=2):
            inbound_units = _parse_int(
                row.get("inbound_units"),
                row_number,
                "inbound_units",
                default=0,
            )
            inbound_units += _parse_int(
                row.get("inbound_working_units"),
                row_number,
                "inbound_working_units",
                default=0,
            )
            inbound_units += _parse_int(
                row.get("inbound_shipped_units"),
                row_number,
                "inbound_shipped_units",
                default=0,
            )
            inbound_units += _parse_int(
                row.get("inbound_receiving_units"),
                row_number,
                "inbound_receiving_units",
                default=0,
            )
            rows.append(
                ParsedInventoryRow(
                    snapshot_date=_parse_date(row.get("snapshot_date", ""), row_number, "snapshot_date"),
                    sku=_parse_sku(row.get("sku"), row_number),
                    available_units=_parse_int(
                        row.get("available_units"),
                        row_number,
                        "available_units",
                        default=0,
                    ),
                    reserved_units=_parse_int(
                        row.get("reserved_units"),
                        row_number,
                        "reserved_units",
                        default=0,
                    ),
                    inbound_units=inbound_units,
                    days_in_storage=(
                        _parse_int(row.get("days_in_storage"), row_number, "days_in_storage")
                        if (row.get("days_in_storage") or "").strip()
                        else None
                    ),
                    monthly_storage_fee=(
                        _parse_decimal(
                            row.get("monthly_storage_fee"),
                            row_number,
                            "monthly_storage_fee",
                            default=Decimal("0"),
                        )
                        if (row.get("monthly_storage_fee") or "").strip()
                        else None
                    ),
                )
            )

    if not rows:
        raise CSVValidationError("Inventory CSV has no data rows.")

    return rows
