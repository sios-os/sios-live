"""Financial tracking — expenses, bills, account monitoring.

ANUBIS tracks finances to:
- Remind about upcoming bills
- Track expenses and categorize them
- Flag unusual or suspicious charges
- Monitor spending patterns
- Suggest budget adjustments

PRIVACY:
- No bank credentials stored in code
- Uses read-only transaction data (exported or via API)
- All financial data stored locally
- Never uploads financial data
- No financial advice — just tracking and alerts

DATA INPUT:
- CSV import (from bank export)
- JSON import (from budgeting apps)
- Manual entry
- Plaid API (optional, requires account)
"""
from __future__ import annotations

import csv
import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# Transaction types
TXN_DEBIT = "debit"
TXN_CREDIT = "credit"
TXN_TRANSFER = "transfer"
TXN_PAYMENT = "payment"
TXN_FEE = "fee"

# Categories
CAT_HOUSING = "housing"
CAT_FOOD = "food"
CAT_TRANSPORT = "transport"
CAT_UTILITIES = "utilities"
CAT_ENTERTAINMENT = "entertainment"
CAT_HEALTH = "health"
CAT_SHOPPING = "shopping"
CAT_INCOME = "income"
CAT_SAVINGS = "savings"
CAT_DEBT = "debt"
CAT_OTHER = "other"
CAT_UNKNOWN = "unknown"


@dataclass
class Transaction:
    """A financial transaction."""
    txn_id: str
    date: float = 0.0
    amount: float = 0.0  # negative for debits, positive for credits
    description: str = ""
    merchant: str = ""
    category: str = CAT_UNKNOWN
    txn_type: str = TXN_DEBIT
    account: str = ""
    flagged: bool = False
    flag_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "txn_id": self.txn_id,
            "date": self.date,
            "amount": self.amount,
            "description": self.description,
            "merchant": self.merchant,
            "category": self.category,
            "txn_type": self.txn_type,
            "account": self.account,
            "flagged": self.flagged,
            "flag_reason": self.flag_reason,
        }


@dataclass
class Bill:
    """A recurring bill."""
    bill_id: str
    name: str = ""
    amount: float = 0.0
    due_day: int = 1  # day of month
    category: str = CAT_OTHER
    auto_pay: bool = False
    paid: bool = False
    last_paid: float = 0.0
    account: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "bill_id": self.bill_id,
            "name": self.name,
            "amount": self.amount,
            "due_day": self.due_day,
            "category": self.category,
            "auto_pay": self.auto_pay,
            "paid": self.paid,
            "last_paid": self.last_paid,
        }


class FinanceTracker:
    """Financial tracking system.

    Imports transactions, categorizes them, tracks bills, and
    flags unusual spending.
    """

    ACTOR = "anubis.finance"

    def __init__(
        self,
        root: str | Path,
        *,
        monthly_budget: float = 0.0,
        ledger: Any | None = None,
        on_flagged: Callable[[Transaction], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.monthly_budget = monthly_budget
        self.ledger = ledger
        self.on_flagged = on_flagged

        self._state_dir = self.root / "memory" / "finance"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._txns_file = self._state_dir / "transactions.json"
        self._bills_file = self._state_dir / "bills.json"

        self._transactions: dict[str, Transaction] = {}
        self._bills: dict[str, Bill] = {}
        self._category_keywords: dict[str, list[str]] = {
            CAT_FOOD: ["grocery", "restaurant", "food", "cafe", "coffee", "pizza", "doordash", "uber eats", "mcdonald", "burger", "kfc", "subway", "taco"],
            CAT_TRANSPORT: ["gas", "fuel", "uber", "lyft", "parking", "transit", "auto"],
            CAT_UTILITIES: ["electric", "water", "gas", "internet", "phone", "cable"],
            CAT_HOUSING: ["rent", "mortgage", "hoa"],
            CAT_ENTERTAINMENT: ["netflix", "spotify", "movie", "game", "steam", "hulu"],
            CAT_HEALTH: ["pharmacy", "doctor", "hospital", "dental", "medical"],
            CAT_SHOPPING: ["amazon", "walmart", "target", "ebay"],
            CAT_INCOME: ["salary", "payroll", "deposit", "refund"],
        }
        self._load()

    def add_transaction(
        self, amount: float, description: str, date: float = 0,
        merchant: str = "", account: str = "",
    ) -> Transaction:
        """Add a transaction manually."""
        if date == 0:
            date = time.time()

        txn_id = hashlib.sha256(
            f"txn:{description}:{amount}:{date}".encode()
        ).hexdigest()[:16]

        txn_type = TXN_CREDIT if amount > 0 else TXN_DEBIT
        category = self._categorize(description, merchant)

        txn = Transaction(
            txn_id=txn_id,
            date=date,
            amount=amount,
            description=description,
            merchant=merchant,
            category=category,
            txn_type=txn_type,
            account=account,
        )

        # Check for unusual activity
        self._check_unusual(txn)

        self._transactions[txn_id] = txn
        self._save_txns()

        if txn.flagged and self.on_flagged:
            try:
                self.on_flagged(txn)
            except Exception:
                pass

        return txn

    def import_csv(self, csv_content: str) -> int:
        """Import transactions from CSV (bank export format)."""
        count = 0
        reader = csv.reader(csv_content.splitlines())
        for row in reader:
            if len(row) < 3:
                continue
            # Try common CSV formats: date, description, amount
            try:
                date_str = row[0]
                description = row[1] if len(row) > 1 else ""
                amount_str = row[2] if len(row) > 2 else "0"
                amount = float(amount_str.replace("$", "").replace(",", ""))

                # Parse date
                from datetime import datetime
                try:
                    date = datetime.strptime(date_str, "%m/%d/%Y").timestamp()
                except ValueError:
                    date = time.time()

                self.add_transaction(amount, description, date)
                count += 1
            except (ValueError, IndexError):
                continue
        return count

    def add_bill(
        self, name: str, amount: float, due_day: int = 1,
        category: str = CAT_OTHER, auto_pay: bool = False,
    ) -> Bill:
        """Add a recurring bill."""
        bill_id = hashlib.sha256(
            f"bill:{name}:{time.time()}".encode()
        ).hexdigest()[:16]
        bill = Bill(
            bill_id=bill_id, name=name, amount=amount,
            due_day=due_day, category=category, auto_pay=auto_pay,
        )
        self._bills[bill_id] = bill
        self._save_bills()
        return bill

    def mark_bill_paid(self, bill_id: str) -> bool:
        bill = self._bills.get(bill_id)
        if bill is None:
            return False
        bill.paid = True
        bill.last_paid = time.time()
        self._save_bills()
        return True

    def get_upcoming_bills(self, within_days: int = 7) -> list[dict[str, Any]]:
        """Get bills due within N days."""
        from datetime import datetime, timedelta
        now = datetime.now()
        upcoming: list[dict[str, Any]] = []
        for bill in self._bills.values():
            if bill.paid and bill.last_paid > time.time() - 86400 * 25:
                continue  # paid recently
            due_date = now.replace(day=bill.due_day)
            if due_date < now:
                due_date = (now.replace(day=1) + timedelta(days=32)).replace(day=bill.due_day)
            days_until = (due_date - now).days
            if 0 <= days_until <= within_days:
                d = bill.to_dict()
                d["days_until_due"] = days_until
                upcoming.append(d)
        return sorted(upcoming, key=lambda x: x["days_until_due"])

    def get_spending_by_category(self, days: int = 30) -> dict[str, float]:
        """Get total spending by category in the last N days."""
        cutoff = time.time() - days * 86400
        totals: dict[str, float] = {}
        for txn in self._transactions.values():
            if txn.date < cutoff or txn.amount >= 0:
                continue
            totals[txn.category] = totals.get(txn.category, 0) + abs(txn.amount)
        return totals

    def get_monthly_spending(self) -> float:
        """Get total spending this month."""
        from datetime import datetime
        now = datetime.now()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return sum(
            abs(t.amount) for t in self._transactions.values()
            if t.date >= start.timestamp() and t.amount < 0
        )

    def get_income(self, days: int = 30) -> float:
        """Get total income in the last N days."""
        cutoff = time.time() - days * 86400
        return sum(
            t.amount for t in self._transactions.values()
            if t.date >= cutoff and t.amount > 0
        )

    def _categorize(self, description: str, merchant: str) -> str:
        """Auto-categorize a transaction based on description."""
        text = f"{description} {merchant}".lower()
        for category, keywords in self._category_keywords.items():
            if any(kw in text for kw in keywords):
                return category
        return CAT_UNKNOWN

    def _check_unusual(self, txn: Transaction) -> None:
        """Flag unusual transactions."""
        # Large transaction
        if abs(txn.amount) > 500:
            txn.flagged = True
            txn.flag_reason = f"Large transaction: ${abs(txn.amount):.2f}"

        # Unusual merchant (first time seeing it)
        if txn.merchant:
            seen_before = any(
                t.merchant.lower() == txn.merchant.lower()
                for t in self._transactions.values()
            )
            if not seen_before and abs(txn.amount) > 100:
                txn.flagged = True
                txn.flag_reason = f"New merchant: {txn.merchant}"

        # Late night transaction
        from datetime import datetime
        hour = datetime.fromtimestamp(txn.date).hour if txn.date else 0
        if hour < 4 and abs(txn.amount) > 50:
            txn.flagged = True
            txn.flag_reason = f"Late night transaction ({hour}:00)"

    # --------------------------------------------------- queries

    def get_transactions(self, limit: int = 50) -> list[dict[str, Any]]:
        txns = sorted(self._transactions.values(), key=lambda t: t.date, reverse=True)
        return [t.to_dict() for t in txns[:limit]]

    def get_flagged_transactions(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._transactions.values() if t.flagged]

    def get_bills(self) -> list[dict[str, Any]]:
        return [b.to_dict() for b in self._bills.values()]

    def get_status(self) -> dict[str, Any]:
        return {
            "total_transactions": len(self._transactions),
            "monthly_spending": self.get_monthly_spending(),
            "monthly_income": self.get_income(30),
            "monthly_budget": self.monthly_budget,
            "budget_used_pct": (
                (self.get_monthly_spending() / self.monthly_budget * 100)
                if self.monthly_budget > 0 else 0
            ),
            "flagged_count": len(self.get_flagged_transactions()),
            "upcoming_bills": len(self.get_upcoming_bills()),
            "total_bills": len(self._bills),
        }

    # --------------------------------------------------- persistence

    def _load(self) -> None:
        if self._txns_file.exists():
            try:
                data = json.loads(self._txns_file.read_text(encoding="utf-8"))
                for t_id, t in data.items():
                    self._transactions[t_id] = Transaction(
                        txn_id=t_id,
                        date=t.get("date", 0),
                        amount=t.get("amount", 0),
                        description=t.get("description", ""),
                        merchant=t.get("merchant", ""),
                        category=t.get("category", CAT_UNKNOWN),
                        txn_type=t.get("txn_type", TXN_DEBIT),
                        account=t.get("account", ""),
                        flagged=t.get("flagged", False),
                        flag_reason=t.get("flag_reason", ""),
                    )
            except Exception:
                pass

        if self._bills_file.exists():
            try:
                data = json.loads(self._bills_file.read_text(encoding="utf-8"))
                for b_id, b in data.items():
                    self._bills[b_id] = Bill(
                        bill_id=b_id,
                        name=b.get("name", ""),
                        amount=b.get("amount", 0),
                        due_day=b.get("due_day", 1),
                        category=b.get("category", CAT_OTHER),
                        auto_pay=b.get("auto_pay", False),
                        paid=b.get("paid", False),
                        last_paid=b.get("last_paid", 0),
                    )
            except Exception:
                pass

    def _save_txns(self) -> None:
        data = {t_id: t.to_dict() for t_id, t in self._transactions.items()}
        self._txns_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _save_bills(self) -> None:
        data = {b_id: b.to_dict() for b_id, b in self._bills.items()}
        self._bills_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
