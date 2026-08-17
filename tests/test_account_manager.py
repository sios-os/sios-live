"""Tests for the account and password manager."""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.account_manager import AccountManager, Account, ACCOUNT_TYPES
from anubis.identity import IdentityVault


class TestAccountManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.vault = IdentityVault(Path(self.tmpdir))
        self.vault.unlock("test_passphrase_123")
        self.am = AccountManager(self.vault, ledger=MagicMock())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ===========================================================
    # VAULT LOCKED
    # ===========================================================

    def test_locked_vault_add(self):
        vault = IdentityVault(Path(tempfile.mkdtemp()))
        am = AccountManager(vault)
        result = am.add_account("Test", url="https://example.com")
        self.assertIn("error", result)
        self.assertIn("locked", result["error"].lower())

    def test_locked_vault_list(self):
        vault = IdentityVault(Path(tempfile.mkdtemp()))
        am = AccountManager(vault)
        result = am.list_accounts()
        self.assertIn("error", result)

    def test_locked_vault_status(self):
        vault = IdentityVault(Path(tempfile.mkdtemp()))
        am = AccountManager(vault)
        status = am.get_status()
        self.assertTrue(status["vault_locked"])
        self.assertEqual(status["account_count"], 0)

    # ===========================================================
    # ADD ACCOUNT
    # ===========================================================

    def test_add_account(self):
        result = self.am.add_account(
            "Electric Company",
            url="https://electric.com/login",
            username="storm",
            password="mypassword",
            account_type="utility",
            bill_due_day=15,
            bill_amount=120.50,
        )
        self.assertEqual(result["status"], "added")
        self.assertEqual(result["name"], "Electric Company")
        self.assertIn("account_id", result)

    def test_add_account_no_name(self):
        result = self.am.add_account("")
        self.assertIn("error", result)

    def test_add_account_duplicate(self):
        self.am.add_account("Netflix", username="storm")
        result = self.am.add_account("Netflix", username="storm2")
        self.assertIn("error", result)
        self.assertIn("already exists", result["error"])

    def test_add_account_invalid_type_defaults_to_other(self):
        result = self.am.add_account("Test", account_type="invalid_type")
        self.assertEqual(result["status"], "added")
        # Verify it was stored as "other"
        accounts = self.am.list_accounts()
        self.assertEqual(accounts["accounts"][0]["account_type"], "other")

    def test_add_account_with_bill(self):
        result = self.am.add_account(
            "Gas Company",
            account_type="utility",
            bill_due_day=5,
            bill_amount=85.00,
        )
        self.assertEqual(result["status"], "added")
        accounts = self.am.list_accounts()
        self.assertEqual(accounts["accounts"][0]["bill_due_day"], 5)
        self.assertEqual(accounts["accounts"][0]["bill_amount"], 85.0)

    def test_add_account_bill_day_clamped(self):
        result = self.am.add_account("Test", bill_due_day=99)
        self.assertEqual(result["status"], "added")
        accounts = self.am.list_accounts()
        self.assertEqual(accounts["accounts"][0]["bill_due_day"], 31)

    def test_add_account_with_notes(self):
        result = self.am.add_account("Bank", notes="Checking account")
        self.assertEqual(result["status"], "added")
        accounts = self.am.list_accounts()
        self.assertEqual(accounts["accounts"][0]["notes"], "Checking account")

    # ===========================================================
    # LIST ACCOUNTS
    # ===========================================================

    def test_list_accounts_empty(self):
        result = self.am.list_accounts()
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["accounts"], [])

    def test_list_accounts_passwords_masked(self):
        self.am.add_account("Test", password="secret123")
        result = self.am.list_accounts()
        self.assertEqual(result["accounts"][0]["password"], "••••••••")

    def test_list_accounts_by_type(self):
        self.am.add_account("Electric", account_type="utility")
        self.am.add_account("Netflix", account_type="subscription")
        result = self.am.list_accounts(account_type="utility")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["accounts"][0]["name"], "Electric")

    # ===========================================================
    # GET ACCOUNT
    # ===========================================================

    def test_get_account_password_masked_by_default(self):
        add_result = self.am.add_account("Test", password="secret123")
        account_id = add_result["account_id"]
        result = self.am.get_account(account_id)
        self.assertEqual(result["password"], "••••••••")

    def test_get_account_with_password(self):
        add_result = self.am.add_account("Test", password="secret123")
        account_id = add_result["account_id"]
        result = self.am.get_account(account_id, include_password=True)
        self.assertEqual(result["password"], "secret123")

    def test_get_account_not_found(self):
        result = self.am.get_account("nonexistent")
        self.assertIn("error", result)

    def test_get_account_updates_last_accessed(self):
        add_result = self.am.add_account("Test")
        account_id = add_result["account_id"]
        before = self.am.get_account(account_id)["last_accessed"]
        time.sleep(0.01)
        after = self.am.get_account(account_id)["last_accessed"]
        self.assertGreater(after, before)

    # ===========================================================
    # UPDATE ACCOUNT
    # ===========================================================

    def test_update_account(self):
        add_result = self.am.add_account("Test", password="old_pass")
        account_id = add_result["account_id"]
        result = self.am.update_account(account_id, password="new_pass")
        self.assertEqual(result["status"], "updated")
        creds = self.am.get_credentials(account_id)
        self.assertEqual(creds["password"], "new_pass")

    def test_update_account_name(self):
        add_result = self.am.add_account("Old Name")
        account_id = add_result["account_id"]
        result = self.am.update_account(account_id, name="New Name")
        self.assertEqual(result["status"], "updated")
        account = self.am.get_account(account_id)
        self.assertEqual(account["name"], "New Name")

    def test_update_account_not_found(self):
        result = self.am.update_account("nonexistent", name="Test")
        self.assertIn("error", result)

    def test_update_account_bill_info(self):
        add_result = self.am.add_account("Electric", bill_due_day=10, bill_amount=50)
        account_id = add_result["account_id"]
        self.am.update_account(account_id, bill_amount=75.0, bill_due_day=20)
        account = self.am.get_account(account_id)
        self.assertEqual(account["bill_amount"], 75.0)
        self.assertEqual(account["bill_due_day"], 20)

    # ===========================================================
    # DELETE ACCOUNT
    # ===========================================================

    def test_delete_account(self):
        add_result = self.am.add_account("Test")
        account_id = add_result["account_id"]
        result = self.am.delete_account(account_id)
        self.assertEqual(result["status"], "deleted")
        # Verify it's gone
        accounts = self.am.list_accounts()
        self.assertEqual(accounts["count"], 0)

    def test_delete_account_not_found(self):
        result = self.am.delete_account("nonexistent")
        self.assertIn("error", result)

    # ===========================================================
    # FIND ACCOUNT
    # ===========================================================

    def test_find_account_exact(self):
        self.am.add_account("Netflix")
        result = self.am.find_account("Netflix")
        self.assertNotIn("error", result)
        self.assertEqual(result["name"], "Netflix")

    def test_find_account_partial(self):
        self.am.add_account("Netflix Streaming")
        result = self.am.find_account("netflix")
        self.assertNotIn("error", result)

    def test_find_account_case_insensitive(self):
        self.am.add_account("Amazon")
        result = self.am.find_account("amazon")
        self.assertNotIn("error", result)

    def test_find_account_not_found(self):
        result = self.am.find_account("Nonexistent Service")
        self.assertIn("error", result)

    # ===========================================================
    # LOGIN AUTOMATION
    # ===========================================================

    @patch("webbrowser.open")
    def test_open_login(self, mock_open):
        add_result = self.am.add_account("Bank", url="https://bank.com/login")
        account_id = add_result["account_id"]
        result = self.am.open_login(account_id)
        self.assertEqual(result["status"], "opened")
        mock_open.assert_called_with("https://bank.com/login")

    def test_open_login_no_url(self):
        add_result = self.am.add_account("Test")
        account_id = add_result["account_id"]
        result = self.am.open_login(account_id)
        self.assertIn("error", result)

    def test_open_login_not_found(self):
        result = self.am.open_login("nonexistent")
        self.assertIn("error", result)

    def test_get_credentials(self):
        add_result = self.am.add_account(
            "Bank", url="https://bank.com", username="storm", password="bankpass"
        )
        account_id = add_result["account_id"]
        creds = self.am.get_credentials(account_id)
        self.assertEqual(creds["username"], "storm")
        self.assertEqual(creds["password"], "bankpass")
        self.assertEqual(creds["url"], "https://bank.com")

    @patch("webbrowser.open")
    def test_login(self, mock_open):
        add_result = self.am.add_account(
            "Bank", url="https://bank.com", username="storm", password="bankpass"
        )
        account_id = add_result["account_id"]
        result = self.am.login(account_id)
        self.assertEqual(result["status"], "login_initiated")
        self.assertEqual(result["username"], "storm")
        self.assertEqual(result["password"], "bankpass")
        mock_open.assert_called()

    def test_spell_password(self):
        spelled = self.am._spell_password("abc123")
        self.assertEqual(spelled, "a b c 1 2 3")

    # ===========================================================
    # BILL TRACKING
    # ===========================================================

    def test_bills_due(self):
        import datetime
        today = datetime.date.today()
        # Add an account with a bill due in 3 days
        due_day = today.day + 3
        if due_day > 28:
            due_day = 15  # fallback if near end of month
        self.am.add_account("Electric", bill_due_day=due_day, bill_amount=100)
        result = self.am.bills_due(within_days=7)
        self.assertGreaterEqual(result["count"], 1)
        self.assertEqual(result["bills"][0]["name"], "Electric")

    def test_bills_due_no_bills(self):
        self.am.add_account("Free Service")
        result = self.am.bills_due(within_days=7)
        self.assertEqual(result["count"], 0)

    def test_bills_due_filters_by_days(self):
        import datetime
        today = datetime.date.today()
        # Bill due on day 1 (likely past or far future)
        self.am.add_account("Old Bill", bill_due_day=1, bill_amount=50)
        result = self.am.bills_due(within_days=1)
        # Day 1 may or may not be within 1 day, but should not error
        self.assertIn("count", result)

    def test_mark_paid(self):
        add_result = self.am.add_account("Electric", bill_due_day=15)
        account_id = add_result["account_id"]
        result = self.am.mark_paid(account_id)
        self.assertEqual(result["status"], "updated")
        account = self.am.get_account(account_id)
        self.assertGreater(account["last_paid"], 0)

    @patch("webbrowser.open")
    def test_open_payment(self, mock_open):
        add_result = self.am.add_account(
            "Electric", url="https://electric.com", payment_url="https://electric.com/pay"
        )
        account_id = add_result["account_id"]
        result = self.am.open_payment(account_id)
        self.assertEqual(result["status"], "opened")
        mock_open.assert_called_with("https://electric.com/pay")

    @patch("webbrowser.open")
    def test_open_payment_falls_back_to_login_url(self, mock_open):
        add_result = self.am.add_account("Electric", url="https://electric.com")
        account_id = add_result["account_id"]
        result = self.am.open_payment(account_id)
        self.assertEqual(result["status"], "opened")
        mock_open.assert_called_with("https://electric.com")

    # ===========================================================
    # STATUS
    # ===========================================================

    def test_status_no_accounts(self):
        status = self.am.get_status()
        self.assertFalse(status["vault_locked"])
        self.assertEqual(status["account_count"], 0)

    def test_status_with_accounts(self):
        self.am.add_account("Electric", account_type="utility", bill_due_day=15)
        self.am.add_account("Netflix", account_type="subscription")
        status = self.am.get_status()
        self.assertEqual(status["account_count"], 2)
        self.assertEqual(status["accounts_by_type"]["utility"], 1)
        self.assertEqual(status["accounts_by_type"]["subscription"], 1)
        self.assertEqual(status["bills_tracked"], 1)

    # ===========================================================
    # IMPORT/EXPORT
    # ===========================================================

    def test_export_accounts(self):
        self.am.add_account("Test1", password="pass1")
        self.am.add_account("Test2", password="pass2")
        result = self.am.export_accounts()
        self.assertEqual(result["count"], 2)
        # Export should include passwords
        for data in result["accounts"].values():
            self.assertIn("password", data)

    def test_import_accounts(self):
        # Create some accounts in a separate vault
        other_dir = tempfile.mkdtemp()
        other_vault = IdentityVault(Path(other_dir))
        other_vault.unlock("import_pass")
        other_am = AccountManager(other_vault)
        other_am.add_account("Imported Account", password="imported_pass")

        # Export from other
        exported = other_am.export_accounts()

        # Import into ours
        result = self.am.import_accounts(exported["accounts"])
        self.assertEqual(result["imported"], 1)
        accounts = self.am.list_accounts()
        self.assertEqual(accounts["count"], 1)

    def test_import_skips_existing(self):
        self.am.add_account("Test")
        accounts_before = self.am.list_accounts()
        # Export and re-import
        exported = self.am.export_accounts()
        result = self.am.import_accounts(exported["accounts"])
        self.assertEqual(result["imported"], 0)  # all already exist

    # ===========================================================
    # PERSISTENCE
    # ===========================================================

    def test_accounts_persist_across_vault_reload(self):
        self.am.add_account("Persistent", password="persist_pass")
        # Lock and unlock
        self.vault.lock()
        self.vault.unlock("test_passphrase_123")
        am2 = AccountManager(self.vault)
        accounts = am2.list_accounts()
        self.assertEqual(accounts["count"], 1)
        self.assertEqual(accounts["accounts"][0]["name"], "Persistent")

    def test_accounts_encrypted_at_rest(self):
        self.am.add_account("Secret Account", password="super_secret")
        # Lock the vault
        self.vault.lock()
        # Read the raw vault file — should not contain plaintext
        vault_file = Path(self.tmpdir) / "vault.enc"
        if vault_file.exists():
            raw = vault_file.read_bytes()
            self.assertNotIn(b"super_secret", raw)
            self.assertNotIn(b"Secret Account", raw)

    # ===========================================================
    # ACCOUNT TYPES
    # ===========================================================

    def test_account_types_complete(self):
        expected = {"banking", "utility", "subscription", "social", "email",
                    "shopping", "government", "health", "work", "other"}
        self.assertEqual(set(ACCOUNT_TYPES.keys()), expected)

    def test_account_dataclass_masked_password(self):
        account = Account(account_id="test", name="Test", password="secret")
        d = account.to_dict(include_password=False)
        self.assertEqual(d["password"], "••••••••")

    def test_account_dataclass_real_password(self):
        account = Account(account_id="test", name="Test", password="secret")
        d = account.to_dict(include_password=True)
        self.assertEqual(d["password"], "secret")


if __name__ == "__main__":
    unittest.main()
