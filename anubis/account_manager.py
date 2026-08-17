"""Account and password manager — DEMON handles logins and bills.

This module stores account credentials (usernames, passwords, URLs) in
the encrypted IdentityVault and provides:

1. **Credential storage** — add, update, retrieve, delete accounts
2. **Login automation** — open login pages, fill credentials
3. **Bill tracking** — track due dates, amounts, payment status
4. **Account categories** — banking, utilities, subscriptions, social, etc.
5. **Secure retrieval** — credentials only shown on explicit request

Security:
- All credentials are stored in the encrypted IdentityVault
- The vault must be unlocked with the Creator passphrase
- Credentials are NEVER logged to the evidence ledger
- Retrieval requires explicit Creator request
- Passwords are masked in status/listing output
- All access is logged (account name + action, NOT the credential)

The Creator can say:
- "Add my electric account" → DEMON asks for URL, username, password
- "Log into my bank" → DEMON opens the bank URL, fills the username
- "What bills are due?" → DEMON lists upcoming bills
- "Pay the electric bill" → DEMON opens the payment page
- "Show me my accounts" → DEMON lists all accounts (passwords masked)
- "Update my Netflix password" → DEMON updates the stored credential
"""
from __future__ import annotations

import hashlib
import json
import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ===========================================================
# Account types
# ===========================================================

ACCOUNT_TYPES = {
    "banking": "Banking & Financial",
    "utility": "Utilities (electric, gas, water, internet)",
    "subscription": "Subscriptions (streaming, software, memberships)",
    "social": "Social media",
    "email": "Email accounts",
    "shopping": "Shopping (Amazon, etc.)",
    "government": "Government (taxes, DMV, benefits)",
    "health": "Health & insurance",
    "work": "Work & professional",
    "other": "Other",
}


@dataclass
class Account:
    """A stored account credential."""
    account_id: str
    name: str               # friendly name, e.g. "Electric Company"
    url: str = ""           # login URL
    username: str = ""      # username or email
    password: str = ""      # password (encrypted in vault)
    account_type: str = "other"
    # Bill tracking
    bill_due_day: int = 0       # day of month (1-31), 0 = no recurring bill
    bill_amount: float = 0.0    # estimated amount (0 = variable)
    bill_currency: str = "USD"
    last_paid: float = 0.0      # timestamp of last payment
    payment_url: str = ""       # direct payment URL if different from login
    auto_pay: bool = False
    # Metadata
    notes: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    last_accessed: float = 0.0

    def to_dict(self, *, include_password: bool = False) -> dict[str, Any]:
        d = {
            "account_id": self.account_id,
            "name": self.name,
            "url": self.url,
            "username": self.username,
            "account_type": self.account_type,
            "account_type_label": ACCOUNT_TYPES.get(self.account_type, "Other"),
            "bill_due_day": self.bill_due_day,
            "bill_amount": self.bill_amount,
            "bill_currency": self.bill_currency,
            "last_paid": self.last_paid,
            "payment_url": self.payment_url,
            "auto_pay": self.auto_pay,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_accessed": self.last_accessed,
        }
        if include_password:
            d["password"] = self.password
        else:
            d["password"] = "••••••••"  # masked
        return d


class AccountManager:
    """Manages account credentials and bill tracking.

    Credentials are stored in the encrypted IdentityVault under the
    "accounts" key as a JSON object. The vault must be unlocked
    with the Creator passphrase before any operation.

    All access is logged to the evidence ledger with the account name
    and action, but NEVER the credential itself.
    """

    ACTOR = "anubis.account_manager"
    VAULT_KEY = "accounts"

    def __init__(
        self,
        vault: Any,
        *,
        ledger: Any | None = None,
        on_speak: Callable[[str], None] | None = None,
    ) -> None:
        self.vault = vault
        self.ledger = ledger
        self.on_speak = on_speak

    def _speak(self, text: str) -> None:
        if self.on_speak:
            try:
                self.on_speak(text)
            except Exception:
                pass

    def _check_unlocked(self) -> bool:
        """Check if the vault is unlocked."""
        if hasattr(self.vault, "is_unlocked"):
            return self.vault.is_unlocked()
        return False

    def _load_accounts(self) -> dict[str, dict]:
        """Load all accounts from the vault."""
        if not self._check_unlocked():
            return {}
        data = self.vault.retrieve(self.VAULT_KEY)
        if data is None:
            return {}
        return data if isinstance(data, dict) else {}

    def _save_accounts(self, accounts: dict[str, dict]) -> bool:
        """Save accounts to the vault."""
        if not self._check_unlocked():
            return False
        return self.vault.store(self.VAULT_KEY, accounts)

    def _log(self, action: str, account_name: str, extra: dict | None = None) -> None:
        """Log an action — NEVER logs credentials."""
        entry = {"action": action, "account": account_name, "timestamp": time.time()}
        if extra:
            entry.update(extra)
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, {"account": account_name, **(extra or {})})
            except Exception:
                pass

    # ===========================================================
    # ACCOUNT CRUD
    # ===========================================================

    def add_account(
        self,
        name: str,
        url: str = "",
        username: str = "",
        password: str = "",
        account_type: str = "other",
        bill_due_day: int = 0,
        bill_amount: float = 0.0,
        payment_url: str = "",
        auto_pay: bool = False,
        notes: str = "",
    ) -> dict[str, Any]:
        """Add a new account."""
        if not self._check_unlocked():
            return {"error": "Vault is locked. Unlock with your passphrase first."}
        if not name.strip():
            return {"error": "Account name is required"}

        accounts = self._load_accounts()

        # Check for duplicate
        for existing in accounts.values():
            if existing.get("name", "").lower() == name.lower():
                return {"error": f"Account '{name}' already exists. Use update instead."}

        account_id = hashlib.sha256(
            f"account:{name}:{time.time()}".encode()
        ).hexdigest()[:16]

        account = Account(
            account_id=account_id,
            name=name.strip(),
            url=url.strip(),
            username=username.strip(),
            password=password,
            account_type=account_type if account_type in ACCOUNT_TYPES else "other",
            bill_due_day=max(0, min(31, bill_due_day)),
            bill_amount=max(0.0, bill_amount),
            payment_url=payment_url.strip(),
            auto_pay=auto_pay,
            notes=notes.strip(),
            created_at=time.time(),
            updated_at=time.time(),
        )

        accounts[account_id] = account.to_dict(include_password=True)
        self._save_accounts(accounts)
        self._log("add_account", name, {"type": account_type})
        return {
            "status": "added",
            "account_id": account_id,
            "name": name,
            "message": f"Account '{name}' added successfully.",
        }

    def update_account(self, account_id: str, **kwargs) -> dict[str, Any]:
        """Update an existing account. Only provided fields are changed."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        accounts = self._load_accounts()
        if account_id not in accounts:
            return {"error": "Account not found"}

        account_data = accounts[account_id]
        for key, value in kwargs.items():
            if key in ("name", "url", "username", "password", "account_type",
                       "bill_due_day", "bill_amount", "bill_currency",
                       "payment_url", "auto_pay", "notes", "last_paid"):
                if value is not None:
                    if key == "bill_due_day":
                        value = max(0, min(31, int(value)))
                    elif key == "bill_amount":
                        value = max(0.0, float(value))
                    elif key == "auto_pay":
                        value = bool(value)
                    account_data[key] = value

        account_data["updated_at"] = time.time()
        accounts[account_id] = account_data
        self._save_accounts(accounts)
        self._log("update_account", account_data.get("name", ""))
        return {
            "status": "updated",
            "account_id": account_id,
            "name": account_data.get("name", ""),
            "message": f"Account '{account_data.get('name', '')}' updated.",
        }

    def delete_account(self, account_id: str) -> dict[str, Any]:
        """Delete an account."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        accounts = self._load_accounts()
        if account_id not in accounts:
            return {"error": "Account not found"}
        name = accounts[account_id].get("name", "")
        del accounts[account_id]
        self._save_accounts(accounts)
        self._log("delete_account", name)
        return {"status": "deleted", "message": f"Account '{name}' deleted."}

    def get_account(self, account_id: str, include_password: bool = False) -> dict[str, Any]:
        """Get a single account."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        accounts = self._load_accounts()
        if account_id not in accounts:
            return {"error": "Account not found"}
        account_data = accounts[account_id]
        # Update last accessed
        account_data["last_accessed"] = time.time()
        accounts[account_id] = account_data
        self._save_accounts(accounts)
        self._log("get_account", account_data.get("name", ""))
        # Build response
        account = Account(**{k: account_data.get(k) for k in Account.__dataclass_fields__})
        return account.to_dict(include_password=include_password)

    def list_accounts(self, account_type: str = "") -> dict[str, Any]:
        """List all accounts. Passwords are always masked."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        accounts = self._load_accounts()
        result = []
        for aid, data in accounts.items():
            if account_type and data.get("account_type") != account_type:
                continue
            account = Account(**{k: data.get(k) for k in Account.__dataclass_fields__})
            result.append(account.to_dict(include_password=False))
        self._log("list_accounts", f"({len(result)} accounts)")
        return {
            "count": len(result),
            "accounts": result,
        }

    def find_account(self, name: str) -> dict[str, Any]:
        """Find an account by name (fuzzy match)."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        accounts = self._load_accounts()
        name_lower = name.lower().strip()
        # Exact match first
        for aid, data in accounts.items():
            if data.get("name", "").lower() == name_lower:
                return {"account_id": aid, **data}
        # Partial match
        for aid, data in accounts.items():
            if name_lower in data.get("name", "").lower():
                return {"account_id": aid, **data}
        return {"error": f"No account found matching '{name}'"}

    # ===========================================================
    # LOGIN AUTOMATION
    # ===========================================================

    def open_login(self, account_id: str) -> dict[str, Any]:
        """Open the login page for an account in the browser."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        accounts = self._load_accounts()
        if account_id not in accounts:
            return {"error": "Account not found"}
        account = accounts[account_id]
        url = account.get("url", "")
        if not url:
            return {"error": "No URL set for this account"}
        try:
            webbrowser.open(url)
            # Update last accessed
            account["last_accessed"] = time.time()
            accounts[account_id] = account
            self._save_accounts(accounts)
            self._log("open_login", account.get("name", ""))
            return {
                "status": "opened",
                "url": url,
                "username": account.get("username", ""),
                "message": f"Opened login page for {account.get('name', '')}. Username: {account.get('username', '(none)')}",
            }
        except Exception as e:
            return {"error": str(e)}

    def get_credentials(self, account_id: str) -> dict[str, Any]:
        """Get full credentials for an account (including password).

        This is for DEMON to speak or display the password when the
        Creator explicitly asks. The request is logged.
        """
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        accounts = self._load_accounts()
        if account_id not in accounts:
            return {"error": "Account not found"}
        account = accounts[account_id]
        self._log("get_credentials", account.get("name", ""), {"reason": "explicit_request"})
        return {
            "name": account.get("name", ""),
            "url": account.get("url", ""),
            "username": account.get("username", ""),
            "password": account.get("password", ""),
        }

    def login(self, account_id: str) -> dict[str, Any]:
        """Open the login page and provide credentials.

        Opens the login URL in the browser and speaks the username
        and password so the Creator can type them in (or DEMON can
        use keyboard automation to fill them).
        """
        creds = self.get_credentials(account_id)
        if "error" in creds:
            return creds
        # Open the login page
        open_result = self.open_login(account_id)
        # Speak the credentials
        username = creds.get("username", "")
        password = creds.get("password", "")
        if username and password:
            self._speak(
                f"Opening {creds.get('name', '')}. "
                f"Your username is {username}. "
                f"Your password is {self._spell_password(password)}."
            )
        elif username:
            self._speak(f"Opening {creds.get('name', '')}. Your username is {username}.")
        return {
            "status": "login_initiated",
            "name": creds.get("name", ""),
            "url": creds.get("url", ""),
            "username": username,
            "password": password,
            "message": f"Login page opened for {creds.get('name', '')}.",
        }

    def _spell_password(self, password: str) -> str:
        """Spell out a password character by character for voice output."""
        return " ".join(list(password))

    # ===========================================================
    # BILL TRACKING
    # ===========================================================

    def bills_due(self, within_days: int = 7) -> dict[str, Any]:
        """Get bills due within the next N days."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        accounts = self._load_accounts()
        import datetime
        today = datetime.date.today()
        bills = []
        for aid, data in accounts.items():
            due_day = data.get("bill_due_day", 0)
            if due_day == 0:
                continue
            # Calculate next due date
            try:
                due_date = today.replace(day=min(due_day, 28))
                if due_date < today:
                    # Move to next month
                    if today.month == 12:
                        due_date = due_date.replace(year=today.year + 1, month=1)
                    else:
                        due_date = due_date.replace(month=today.month + 1)
                days_until = (due_date - today).days
                if days_until <= within_days:
                    bills.append({
                        "account_id": aid,
                        "name": data.get("name", ""),
                        "due_date": due_date.isoformat(),
                        "days_until": days_until,
                        "amount": data.get("bill_amount", 0),
                        "currency": data.get("bill_currency", "USD"),
                        "auto_pay": data.get("auto_pay", False),
                        "payment_url": data.get("payment_url", "") or data.get("url", ""),
                        "last_paid": data.get("last_paid", 0),
                    })
            except Exception:
                pass
        # Sort by days until due
        bills.sort(key=lambda b: b["days_until"])
        self._log("bills_due", f"({len(bills)} bills)")
        return {
            "count": len(bills),
            "bills": bills,
            "message": f"{len(bills)} bill{'s' if len(bills) != 1 else ''} due in the next {within_days} days.",
        }

    def mark_paid(self, account_id: str) -> dict[str, Any]:
        """Mark a bill as paid."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        return self.update_account(account_id, last_paid=time.time())

    def open_payment(self, account_id: str) -> dict[str, Any]:
        """Open the payment page for an account."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        accounts = self._load_accounts()
        if account_id not in accounts:
            return {"error": "Account not found"}
        account = accounts[account_id]
        url = account.get("payment_url", "") or account.get("url", "")
        if not url:
            return {"error": "No payment URL set for this account"}
        try:
            webbrowser.open(url)
            self._log("open_payment", account.get("name", ""))
            return {
                "status": "opened",
                "url": url,
                "message": f"Opened payment page for {account.get('name', '')}.",
            }
        except Exception as e:
            return {"error": str(e)}

    # ===========================================================
    # STATUS
    # ===========================================================

    def get_status(self) -> dict[str, Any]:
        """Get account manager status (no credentials revealed)."""
        if not self._check_unlocked():
            return {"vault_locked": True, "account_count": 0}
        accounts = self._load_accounts()
        # Count by type
        by_type: dict[str, int] = {}
        bills_count = 0
        for data in accounts.values():
            t = data.get("account_type", "other")
            by_type[t] = by_type.get(t, 0) + 1
            if data.get("bill_due_day", 0) > 0:
                bills_count += 1
        return {
            "vault_locked": False,
            "account_count": len(accounts),
            "accounts_by_type": by_type,
            "bills_tracked": bills_count,
        }

    # ===========================================================
    # IMPORT/EXPORT
    # ===========================================================

    def export_accounts(self) -> dict[str, Any]:
        """Export all accounts (for backup). Includes passwords."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        accounts = self._load_accounts()
        self._log("export_accounts", f"({len(accounts)} accounts)")
        return {"accounts": accounts, "count": len(accounts)}

    def import_accounts(self, accounts_data: dict[str, dict]) -> dict[str, Any]:
        """Import accounts from a backup."""
        if not self._check_unlocked():
            return {"error": "Vault is locked."}
        existing = self._load_accounts()
        imported = 0
        for aid, data in accounts_data.items():
            if aid not in existing:
                existing[aid] = data
                imported += 1
        self._save_accounts(existing)
        self._log("import_accounts", f"({imported} new)")
        return {"imported": imported, "total": len(existing)}
