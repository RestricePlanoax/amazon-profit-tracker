from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


class CSVValidationError(ValueError):
    pass


ORDERS_REQUIRED_COLUMNS = {
    "order_date",
    "order_id",
    "sku",
    "units",
    "revenue",
    "fees",
    "refund",
}

ADS_REQUIRED_COLUMNS = {"date", "sku", "spend", "sales", "clicks", "impressions"}
SETTLEMENT_REQUIRED_COLUMNS = {
    "settlement_date",
    "settlement_id",
    "total_amount",
    "fees",
    "taxes",
    "reimbursements",
}

ORDERS_COLUMN_ALIASES = {
    "order_date": {"order_date", "purchase_date", "orderdate", "date"},
    "order_id": {"order_id", "amazon_order_id", "amazonorderid"},
    "sku": {"sku", "seller_sku", "merchant_sku"},
    "units": {"units", "quantity", "quantity_ordered", "units_ordered"},
    "revenue": {"revenue", "sales", "item_price", "principal", "sales_amount"},
    "fees": {"fees", "fee", "commission", "commission_amount", "amazon_fees"},
    "refund": {"refund", "refund_amount", "refunds"},
}

ADS_COLUMN_ALIASES = {
    "date": {"date", "day"},
    "sku": {"sku", "seller_sku", "advertised_sku"},
    "spend": {"spend", "cost"},
    "sales": {"sales", "ad_sales", "attributed_sales_7d", "seven_day_total_sales"},
    "clicks": {"clicks"},
    "impressions": {"impressions"},
}

SETTLEMENT_COLUMN_ALIASES = {
    "settlement_date": {"settlement_date", "posted_date", "date", "settlement_start_date"},
    "settlement_id": {"settlement_id", "settlementid", "id"},
    "total_amount": {"total_amount", "amount", "total"},
    "fees": {"fees", "total_fees", "amazon_fees"},
    "taxes": {"taxes", "tax_amount", "tax"},
    "reimbursements": {"reimbursements", "reimbursement", "reimbursement_amount"},
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


def normalize_column_name(name: str) -> str:
    normalized = name.strip().lower()
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized


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
                if alternate_columns.issubset(available):
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
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CSVValidationError(
            f"Row {row_number}: '{column_name}' must be in YYYY-MM-DD format."
        ) from exc


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


def parse_orders_csv(file_path: str | Path) -> list[ParsedOrderRow]:
    rows: list[ParsedOrderRow] = []
    with Path(file_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = _prepare_reader(handle, ORDERS_COLUMN_ALIASES)
        _ensure_required_columns(
            reader,
            ORDERS_REQUIRED_COLUMNS,
            upload_type="orders",
            alternate_datasets={
                "ads": ADS_REQUIRED_COLUMNS,
                "settlement": SETTLEMENT_REQUIRED_COLUMNS,
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
                "orders": ORDERS_REQUIRED_COLUMNS,
                "settlement": SETTLEMENT_REQUIRED_COLUMNS,
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
                "orders": ORDERS_REQUIRED_COLUMNS,
                "ads": ADS_REQUIRED_COLUMNS,
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
