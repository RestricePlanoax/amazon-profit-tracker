from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reimbursement import Reimbursement


def _decimal(value: Decimal | None) -> Decimal:
    return value or Decimal("0")


class ReimbursementService:
    def get_reimbursements(self, db: Session, store_id) -> dict:
        cases = db.scalars(
            select(Reimbursement)
            .where(Reimbursement.store_id == store_id)
            .order_by(Reimbursement.received.asc(), Reimbursement.claim_deadline.asc())
        ).all()
        today = date.today()
        total_pending_amount = sum(
            _decimal(case.amount)
            for case in cases
            if not case.received
        )
        near_expiry_count = sum(
            1
            for case in cases
            if not case.received
            and case.claim_deadline is not None
            and case.claim_deadline <= today + timedelta(days=14)
        )
        open_cases = sum(1 for case in cases if not case.received)
        return {
            "summary": {
                "total_pending_amount": round(float(total_pending_amount), 2),
                "near_expiry_count": near_expiry_count,
                "open_cases": open_cases,
            },
            "cases": cases,
        }
